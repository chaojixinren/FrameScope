import re


def replace_content_markers(markdown: str, video_id: str, platform: str = 'bilibili') -> str:
    """
    替换 *Content-04:16*、Content-04:16 或 Content-[04:16] 为超链接，跳转到对应平台视频的时间位置
    """
    # 匹配三种形式：*Content-04:16*、Content-04:16、Content-[04:16]
    pattern = r"(?:\*?)Content-(?:\[(\d{2}):(\d{2})\]|(\d{2}):(\d{2}))"

    def replacer(match):
        mm = match.group(1) or match.group(3)
        ss = match.group(2) or match.group(4)
        total_seconds = int(mm) * 60 + int(ss)

        if platform == 'bilibili':
            url = f"https://www.bilibili.com/video/{video_id}?t={total_seconds}"
        else:
            return f"({mm}:{ss})"

        return f"[原片 @ {mm}:{ss}]({url})"

    return re.sub(pattern, replacer, markdown)
