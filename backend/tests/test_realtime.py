import asyncio
import socket
import struct
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.api.v1.dxcluster import _find_node
from app.config import settings
from app.exceptions import PermissionException
from app.services.dxcluster_manager import DXClusterManager, NodeInfo
from app.services.udp_listener_service import UDPListenerService, WSJTXProtocol, N1MMProtocol


def utf8(value):
    encoded = value.encode('utf-8')
    return struct.pack('>I', len(encoded)) + encoded


def qdatetime(instant):
    julian = instant.date().toordinal() + 1721425
    ms = ((instant.hour * 60 + instant.minute) * 60 + instant.second) * 1000
    return struct.pack('>qIB', julian, ms, 1)


def qso_packet():
    instant = datetime(2026, 1, 2, 12, 34, 56, tzinfo=timezone.utc)
    data = struct.pack('>III', 0xADBCCBDA, 3, 5) + utf8('WSJT-X')
    data += qdatetime(instant) + utf8('JA1ABC') + utf8('PM95') + struct.pack('>Q', 14074000)
    for value in ('FT8', '-10', '-05', '25W', '测试', 'Operator'):
        data += utf8(value)
    data += qdatetime(instant)
    for value in ('BA1ABC', 'BA1ABC', 'OM89AA'):
        data += utf8(value)
    return data


def test_standard_wsjtx_qso_and_invalid_packets(monkeypatch):
    monkeypatch.setattr(settings, 'UDP_ALLOWED_SOURCES', ['127.0.0.1'])
    received = []
    protocol = WSJTXProtocol(received.append)
    packet = qso_packet()
    protocol.datagram_received(packet, ('127.0.0.1', 50000))
    assert received[0]['dxCall'] == 'JA1ABC'
    assert received[0]['txFrequency'] == 14074000
    assert received[0]['comments'] == '测试'
    assert received[0]['timeOn'] == 1767357296000
    protocol.datagram_received(packet, ('10.0.0.1', 50000))
    protocol.datagram_received(packet[:30], ('127.0.0.1', 50000))
    protocol.datagram_received(struct.pack('>III', 0xADBCCBDA, 3, 3) + utf8('WSJT-X'), ('127.0.0.1', 50000))
    assert len(received) == 1


def test_n1mm_rejects_entities_and_untrusted_sender(monkeypatch):
    monkeypatch.setattr(settings, 'UDP_ALLOWED_SOURCES', ['127.0.0.1'])
    received = []
    protocol = N1MMProtocol(received.append)
    protocol.datagram_received(b'<contactinfo><call>JA1ABC</call></contactinfo>', ('127.0.0.1', 12345))
    assert received == [{'call': 'JA1ABC'}]
    protocol.datagram_received(b'<!DOCTYPE x [<!ENTITY v "secret">]><contactinfo><call>&v;</call></contactinfo>', ('127.0.0.1', 12345))
    protocol.datagram_received(b'<contactinfo><call>JA2ABC</call></contactinfo>', ('10.0.0.1', 12345))
    assert received == [{'call': 'JA1ABC'}]


def reserve_ports():
    first = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    second = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    first.bind(('127.0.0.1', 0))
    second.bind(('127.0.0.1', 0))
    ports = first.getsockname()[1], second.getsockname()[1]
    first.close()
    second.close()
    return ports


@pytest.mark.asyncio
async def test_udp_owner_isolation_and_port_release(monkeypatch):
    monkeypatch.setattr(settings, 'UDP_BIND_HOST', '127.0.0.1')
    monkeypatch.setattr(settings, 'UDP_ALLOWED_SOURCES', ['127.0.0.1'])
    listener = UDPListenerService()
    first, second = reserve_ports()
    own = listener.subscribe(1)
    foreign = listener.subscribe(2)
    try:
        await listener.start(1, first, second)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender:
            sender.sendto(qso_packet(), ('127.0.0.1', first))
        event = await asyncio.wait_for(own.get(), timeout=2)
        assert event['data']['call_sign'] == 'JA1ABC'
        assert event['data']['band'] == '20m'
        assert event['data']['freq'] == '14.074'
        assert foreign.empty()
        assert listener.status_for(2)['last_qso'] is None
        assert listener.status_for(2)['qso_count'] == 0
        with pytest.raises(PermissionException):
            await listener.stop(2)
        with pytest.raises(PermissionException):
            await listener.start(2, first, second)
    finally:
        await listener.stop()
        listener.unsubscribe(own)
        listener.unsubscribe(foreign)
    for port in (first, second):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.bind(('127.0.0.1', port))
    await listener.start(1, first, second)
    await listener.stop(1)


@pytest.mark.asyncio
async def test_udp_bind_failure_does_not_report_running(monkeypatch):
    monkeypatch.setattr(settings, 'UDP_BIND_HOST', '127.0.0.1')
    listener = UDPListenerService()
    first, second = reserve_ports()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as occupied:
        occupied.bind(('127.0.0.1', second))
        with pytest.raises(OSError):
            await listener.start(1, first, second)
    assert not listener.is_running
    await listener.start(1, first, second)
    await listener.stop()


@pytest.mark.asyncio
async def test_unconfigured_dx_endpoint_rejected_without_connection():
    with pytest.raises(HTTPException) as error:
        _find_node('127.0.0.1', 6379)
    assert error.value.status_code == 422
    with pytest.raises(ValueError, match='not configured'):
        await DXClusterManager().connect(NodeInfo('127.0.0.1', 6379, 'invalid', 'invalid'), 'BA1ABC')


@pytest.mark.asyncio
async def test_configured_dx_connection_closes_socket_and_notifies(monkeypatch):
    accepted = asyncio.Future()
    peer_closed = asyncio.Event()

    async def node(reader, writer):
        writer.write(b'login:\n')
        await writer.drain()
        accepted.set_result(await reader.readline())
        await reader.read()
        writer.close()
        await writer.wait_closed()
        peer_closed.set()

    server = await asyncio.start_server(node, '127.0.0.1', 0)
    port = server.sockets[0].getsockname()[1]
    monkeypatch.setattr(settings, 'DX_CLUSTER_NODES', [f'127.0.0.1:{port}'])
    manager = DXClusterManager()
    queue = await manager.subscribe()
    try:
        await manager.connect(_find_node('127.0.0.1', port), 'BA1ABC')
        assert await asyncio.wait_for(accepted, 2) == b'BA1ABC\n'
        assert manager.connected
        await manager.disconnect()
        await asyncio.wait_for(peer_closed.wait(), 2)
        assert (await queue.get())['type'] == 'disconnect'
        assert not manager.connected
    finally:
        await manager.disconnect()
        await manager.unsubscribe(queue)
        server.close()
        await server.wait_closed()
