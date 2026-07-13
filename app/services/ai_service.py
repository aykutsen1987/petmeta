"""
Yapay Zekâ Analiz Servisi.

Android istemcisi bir fotoğrafı `/analysis` endpoint'ine multipart olarak
gönderir; bu servis fotoğrafı base64'e çevirip Groq'un görsel (vision)
destekli chat completion API'sine gönderir ve modelden YALNIZCA JSON
formatında, önceden tanımlanmış bir şemaya uyan bir yanıt üretmesini ister.

ÖNEMLİ - Sorumluluk Reddi: Bu servisin ürettiği sonuç KESİNLİKLE bir teşhis
değildir; her yanıt DEFAULT_DISCLAIMER metnini içerir ve Android tarafında
kullanıcıya mutlaka gösterilir (bkz. AiAnalysisResponseDto.disclaimer).
"""
import base64
import json
import logging

import httpx

from app.config import settings
from app.schemas.analysis import DEFAULT_DISCLAIMER, AiFindingSchema

logger = logging.getLogger("petmeta.ai_service")

_SYSTEM_PROMPT = (
    "Sen bir evcil hayvan cilt/tüy/genel görünüm ön değerlendirme asistanısın. "
    "Sana verilen fotoğrafı incele ve YALNIZCA aşağıdaki JSON şemasına uyan, "
    "başka hiçbir açıklama veya metin içermeyen bir JSON nesnesi döndür:\n"
    "{\n"
    '  "findings": [{"condition": string, "probabilityPercent": 0-100, '
    '"riskLevel": "LOW"|"MEDIUM"|"HIGH"}],\n'
    '  "vetRecommendation": string,\n'
    '  "preventiveCareRecommendation": string,\n'
    '  "nutritionRecommendation": string,\n'
    '  "hygieneRecommendation": string\n'
    "}\n"
    "Tüm metinleri Türkçe yaz. Kesin bir teşhis koyma; yalnızca olası durumları ve "
    "genel önerileri paylaş. Emin olmadığın durumlarda riskLevel değerini LOW veya "
    "MEDIUM olarak işaretle ve mutlaka bir veterinere danışılmasını öner."
)


class AiAnalysisResult:
    def __init__(
        self,
        findings: list[AiFindingSchema],
        vet_recommendation: str,
        preventive_care_recommendation: str,
        nutrition_recommendation: str,
        hygiene_recommendation: str,
    ) -> None:
        self.findings = findings
        self.vet_recommendation = vet_recommendation
        self.preventive_care_recommendation = preventive_care_recommendation
        self.nutrition_recommendation = nutrition_recommendation
        self.hygiene_recommendation = hygiene_recommendation


def _fallback_result(reason: str) -> AiAnalysisResult:
    """
    Groq API anahtarı tanımlı değilse veya çağrı başarısız olursa kullanılan
    güvenli varsayılan yanıt. Kullanıcıyı asla teknik bir hata mesajıyla baş
    başa bırakmaz; bunun yerine her zaman veterinere yönlendiren, temkinli bir
    genel öneri seti döndürür.
    """
    logger.warning("AI analizi geri düşüş (fallback) yanıtı kullanılıyor: %s", reason)
    return AiAnalysisResult(
        findings=[
            AiFindingSchema(condition="Belirsiz / Değerlendirilemedi", probability_percent=0, risk_level="LOW")
        ],
        vet_recommendation=(
            "Fotoğraf otomatik olarak değerlendirilemedi. Herhangi bir belirti "
            "(kaşıntı, kızarıklık, tüy dökülmesi vb.) fark ederseniz lütfen bir "
            "veteriner hekime başvurun."
        ),
        preventive_care_recommendation="Düzenli veteriner kontrollerini ve aşı takvimini aksatmayın.",
        nutrition_recommendation="Yaşına ve türüne uygun, dengeli bir beslenme programı sürdürün.",
        hygiene_recommendation="Düzenli tımar ve temizlik rutinlerine devam edin.",
    )


async def analyze_pet_photo(photo_bytes: bytes, content_type: str) -> AiAnalysisResult:
    if not settings.groq_api_key:
        return _fallback_result("GROQ_API_KEY tanımlı değil.")

    base64_image = base64.b64encode(photo_bytes).decode("utf-8")
    data_url = f"data:{content_type};base64,{base64_image}"

    request_body = {
        "model": settings.groq_model,
        "temperature": 0.2,
        "max_tokens": 1024,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Bu evcil hayvan fotoğrafını değerlendir."},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.groq_api_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                json=request_body,
            )
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError as exc:
        return _fallback_result(f"Groq API isteği başarısız oldu: {exc}")

    try:
        message_content = payload["choices"][0]["message"]["content"]
        parsed = json.loads(message_content)

        findings = [
            AiFindingSchema(
                condition=item["condition"],
                probability_percent=int(item["probabilityPercent"]),
                risk_level=item["riskLevel"],
            )
            for item in parsed.get("findings", [])
        ] or [AiFindingSchema(condition="Belirgin bir bulgu yok", probability_percent=0, risk_level="LOW")]

        return AiAnalysisResult(
            findings=findings,
            vet_recommendation=parsed.get("vetRecommendation", DEFAULT_DISCLAIMER),
            preventive_care_recommendation=parsed.get("preventiveCareRecommendation", ""),
            nutrition_recommendation=parsed.get("nutritionRecommendation", ""),
            hygiene_recommendation=parsed.get("hygieneRecommendation", ""),
        )
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        return _fallback_result(f"Groq API yanıtı beklenen şemaya uymuyor: {exc}")
