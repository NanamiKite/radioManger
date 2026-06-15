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

            record = {}
            # 大小写不敏感提取所有标签
            pattern = r"<([A-Z_]+)(?::(\d+))?>(.*?)(?=<[A-Z_]+|$)"
            matches = re.finditer(pattern, entry, re.DOTALL | re.IGNORECASE)

            for match in matches:
                tag_name = match.group(1)
                tag_value = match.group(3).strip()
                record[tag_name.lower()] = tag_value

            if record:
                records.append(record)

        return records

    @staticmethod
    def generate_adi_file(logs: List[Dict]) -> str:
        """生成ADI文件"""
        content = "ADIF Export\n<eoh>\n"

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
            'station_callsign': 'station_callsign',
            'distance': 'distance',
            'comment': 'comment',
        }

        for adi_key, adi_value in adi_record.items():
            app_key = field_map.get(adi_key.lower())
            if app_key:
                mapped[app_key] = adi_value

        return mapped
