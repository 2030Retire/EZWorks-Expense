"""
OCR Module - Claude API를 사용하여 영수증 이미지에서 데이터 추출
"""
import base64
import json
import re
from datetime import datetime
from pathlib import Path

import anthropic


CATEGORY_MAP = {
    "LUNCH": "LUNCH",
    "DINNER": "DINNER",
    "ENTERTAINMENT": "ENTERTAINMENT",
    "TAXI": "TAXI",
    "TRANSPORT": "OTHER TRANSPORT'N",
    "MISC": "MISCELLANEOUS",
    "TELEPHONE": "TELEPHONE/INTERNET",
}

OCR_PROMPT_TEMPLATE = """이 영수증 이미지를 분석해서 다음 정보를 JSON 형식으로 추출해주세요.

추출 항목:
1. date: 날짜 (YYYY-MM-DD 형식. 연도가 없으면 {assume_year}년으로 가정)
2. merchant: 가맹점/상호명 (영문 대문자로 변환, 최대 40자)
3. amount: 합계 금액 (원래 통화 기준, 숫자만. 천원 단위 구분자 제거)
4. currency: 통화 코드 (다음 중 하나: USD, KRW, EUR, JPY, GBP, CNY)
   - 한국 원화 영수증 → KRW
   - 미국 달러 영수증 → USD
   - 통화 기호($, ₩, ¥, €, £)를 참고하세요
5. category: 다음 중 하나로 분류:
   - LUNCH: 점심식사 (1인당 30,000원 이하 또는 낮 시간대)
   - DINNER: 저녁식사 (배달 포함)
   - ENTERTAINMENT: 접대/비즈니스 식사 (50,000원 이상 또는 주류 포함 술자리)
   - TAXI: 택시/우버
   - TRANSPORT: 버스/지하철/KTX 등 대중교통
   - MISC: 편의점, 선물, 기타
   - TELEPHONE: 통신비
6. memo: 간단한 메모 (한국어 OK, 최대 30자)
7. confidence: OCR 인식 신뢰도
   - high: 영수증이 선명하고 모든 정보가 명확히 읽힘
   - medium: 일부 정보가 불확실하거나 흐림
   - low: 이미지가 흐리거나, 글자를 읽기 어렵거나, 영수증이 아닌 것 같음

응답은 반드시 아래 JSON 형식만 출력하세요 (설명 없이):
{{
  "date": "{assume_year}-10-20",
  "merchant": "CAFE EXAMPLE",
  "amount": 19500,
  "currency": "KRW",
  "category": "LUNCH",
  "memo": "점심",
  "confidence": "high"
}}

금액을 찾을 수 없으면 amount를 0으로 설정하세요.
날짜를 찾을 수 없으면 date를 null로 설정하세요."""


def encode_image(image_path: str) -> tuple[str, str]:
    """이미지를 base64로 인코딩하고 미디어 타입 반환"""
    ext = Path(image_path).suffix.lower()
    media_type_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".heic": "image/heic",
        ".gif": "image/gif",
    }
    media_type = media_type_map.get(ext, "image/jpeg")

    with open(image_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")

    return data, media_type


def normalize_category(category: str) -> str:
    """카테고리 정규화"""
    cat_upper = category.upper().strip()
    return CATEGORY_MAP.get(cat_upper, "MISCELLANEOUS")


def process_receipt_image(image_path: str, api_key: str) -> dict:
    """
    단일 영수증 이미지 OCR 처리

    Returns:
        {
            "filename": str,
            "date": str | None,
            "merchant": str,
            "amount": int,
            "currency": str,       # USD, KRW, EUR, JPY, GBP, CNY
            "category": str,
            "memo": str,
            "confidence": str,     # high, medium, low
            "raw_response": str,
            "error": str | None
        }
    """
    filename = Path(image_path).name

    try:
        image_data, media_type = encode_image(image_path)
    except Exception as e:
        return {
            "filename": filename,
            "date": None,
            "merchant": "",
            "amount": 0,
            "currency": "KRW",
            "category": "MISCELLANEOUS",
            "memo": "",
            "confidence": "low",
            "raw_response": "",
            "error": f"이미지 읽기 실패: {str(e)}",
        }

    client = anthropic.Anthropic(api_key=api_key)

    try:
        ocr_prompt = OCR_PROMPT_TEMPLATE.format(assume_year=datetime.now().year)
        message = client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=512,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {"type": "text", "text": ocr_prompt},
                    ],
                }
            ],
        )

        raw_text = message.content[0].text.strip()

        # JSON 추출 (마크다운 코드블록 처리)
        json_match = re.search(r"\{[\s\S]*\}", raw_text)
        if not json_match:
            raise ValueError(f"JSON을 찾을 수 없습니다: {raw_text[:200]}")

        parsed = json.loads(json_match.group())

        currency = (parsed.get("currency") or "KRW").upper().strip()
        # 유효한 통화 코드만 허용
        if currency not in ("USD", "KRW", "EUR", "JPY", "GBP", "CNY"):
            currency = "KRW"

        confidence = (parsed.get("confidence") or "high").lower().strip()
        if confidence not in ("high", "medium", "low"):
            confidence = "medium"

        return {
            "filename": filename,
            "date": parsed.get("date"),
            "merchant": (parsed.get("merchant") or "").upper()[:40],
            "amount": int(parsed.get("amount") or 0),
            "currency": currency,
            "category": normalize_category(parsed.get("category") or "MISC"),
            "memo": (parsed.get("memo") or "")[:30],
            "confidence": confidence,
            "raw_response": raw_text,
            "error": None,
        }

    except Exception as e:
        err_str = str(e)
        # 401: API 키 인증 실패
        if "401" in err_str or "authentication" in err_str.lower() or "invalid x-api-key" in err_str.lower():
            err_msg = "API 키가 유효하지 않습니다. Anthropic 콘솔(console.anthropic.com)에서 키를 확인하고 .env 파일을 업데이트한 뒤 서버를 재시작하세요."
        # 429: 요청 한도 초과
        elif "429" in err_str or "rate limit" in err_str.lower():
            err_msg = "API 요청 한도 초과입니다. 잠시 후 다시 시도하세요."
        # 402: 크레딧 부족
        elif "402" in err_str or "credit" in err_str.lower():
            err_msg = "Anthropic 계정의 크레딧이 부족합니다. console.anthropic.com에서 확인하세요."
        else:
            err_msg = err_str
        return {
            "filename": filename,
            "date": None,
            "merchant": "",
            "amount": 0,
            "currency": "KRW",
            "category": "MISCELLANEOUS",
            "memo": "",
            "confidence": "low",
            "raw_response": "",
            "error": err_msg,
        }
