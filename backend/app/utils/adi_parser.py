import re
from typing import List, Dict

class ADIParser:
    """ADIF/ADI文件解析器 - 兼容 WSJT-X 等软件导出的混合大小写格式"""

    @staticmethod
    def parse_adi_file(content: str) -> List[Dict]:
        """解析ADI文件（大小写不敏感 EOR/EOH）"""
        records = []

        # 大小写不敏感地分割记录
        entries = re.split(r'<eor>', content, flags=re.IGNORECASE)

        for entry in entries:
            if not entry.strip():
                continue

            # 跳过 EOH 头及其之前的内容
            eoh_idx = re.search(r'<eoh>', entry, flags=re.IGNORECASE)
            if eoh_idx:
                entry = entry[eoh_idx.end():]

            if not entry.strip():
                continue

            record = ADIParser._parse_record_fields(entry)

            if record:
                records.append(record)

        return records

    @staticmethod
    def _parse_record_fields(entry: str) -> Dict:
        """解析单条记录的所有字段，使用 length 精确截取值。"""
        record = {}
        pos = 0
        while pos < len(entry):
            # 查找下一个 <TAG
            tag_start = entry.find('<', pos)
            if tag_start == -1:
                break

            # 查找 > 结束标签头
            tag_end = entry.find('>', tag_start)
            if tag_end == -1:
                break

            tag_header = entry[tag_start + 1:tag_end]

            # 解析 TAG_NAME:length 或 TAG_NAME
            if ':' in tag_header:
                parts = tag_header.split(':', 1)
                tag_name = parts[0].strip().upper()
                try:
                    length = int(parts[1].strip())
                except ValueError:
                    length = None
            else:
                tag_name = tag_header.strip().upper()
                length = None

            # 跳过 EOR/EOH 标记
            if tag_name in ('EOR', 'EOH'):
                pos = tag_end + 1
                continue

            # 提取值：优先用 length 精确截取
            if length is not None:
                value = entry[tag_end + 1: tag_end + 1 + length]
                pos = tag_end + 1 + length
            else:
                # 无 length 时，查找下一个 <TAG 作为结束
                next_tag = entry.find('<', tag_end + 1)
                if next_tag == -1:
                    value = entry[tag_end + 1:]
                    pos = len(entry)
                else:
                    value = entry[tag_end + 1:next_tag]
                    pos = next_tag

            record[tag_name.lower()] = value.strip()

        return record

    @staticmethod
    def generate_adi_file(logs: List[Dict]) -> str:
        """生成ADI文件"""
        content = "<ADIF_VER:5>3.1.0 <PROGRAMID:12>RadioManager <EOH>\n"

        for log in logs:
            for key, value in log.items():
                if value is not None:
                    content += f"<{key.upper()}:{len(str(value))}>{value}\n"
            content += "<EOR>\n"

        return content

    @staticmethod
    def map_adi_fields(adi_record: Dict) -> Dict:
        """映射ADI字段到应用字段"""
        mapped = {}

        field_map = {
            'call': 'call_sign',
            'call_sign': 'call_sign',
            'qso_date': 'qso_date',
            'qso_date_off': 'qso_date_off',
            'time_on': 'time_on',
            'time_off': 'time_off',
            'band': 'band',
            'band_rx': 'band_rx',
            'freq': 'freq',
            'freq_rx': 'freq_rx',
            'mode': 'mode',
            'rst_sent': 'rst_sent',
            'rst_rcvd': 'rst_rcvd',
            'gridsquare': 'grid_square',
            'grid_square': 'grid_square',
            'operator': 'operator',
            'qth': 'qth',
            'qsl_sent': 'qsl_sent',
            'qsl_rcvd': 'qsl_rcvd',
            'eqsl_sent': 'eqsl_sent',
            'eqsl_rcvd': 'eqsl_rcvd',
            'lotw_sent': 'lotw_sent',
            'lotw_rcvd': 'lotw_rcvd',
            'tx_pwr': 'tx_pwr',
            'my_gridsquare': 'my_gridsquare',
            'my_grid_square': 'my_gridsquare',
            'my_call': 'my_call',
            'station_callsign': 'station_callsign',
            'distance': 'distance',
            'comment': 'comment',
            'prop_mode': 'prop_mode',
            'sat_name': 'sat_name',
            'srx': 'srx',
            'stx': 'stx',
            'contest_id': 'contest_id',
        }

        for adi_key, adi_value in adi_record.items():
            app_key = field_map.get(adi_key.lower())
            if app_key:
                mapped[app_key] = adi_value

        return mapped
