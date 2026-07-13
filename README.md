# PetMeta Backend (FastAPI)

PetMeta Android uygulamasının backend API'si. Evcil hayvan profilleri, aşı/ilaç/veteriner
takibi, mama/su/egzersiz/kilo kayıtları ve Groq destekli yapay zekâ fotoğraf analizi
uç noktalarını sağlar. Android istemcisi bu API'ye `data/remote/api/PetMetaApiService.kt`
üzerinden Retrofit ile bağlanır.

## Klasör Yapısı

```
app/
├── main.py            # FastAPI uygulama girişi, router kayıtları
├── config.py           # Ortam değişkenlerinden okunan ayarlar (pydantic-settings)
├── database.py          # SQLAlchemy engine/session/Base
├── models/            # SQLAlchemy ORM modelleri (User, Pet, Vaccine, Medicine, ...)
├── schemas/            # Pydantic request/response şemaları (Android DTO'larıyla birebir uyumlu)
├── routers/            # FastAPI APIRouter'ları (auth, pets, vaccines, medicines, ...)
├── services/            # İş mantığı (auth_service, pet_service, ai_service)
└── security/            # JWT üretim/doğrulama, parola hashleme, get_current_user
```

## Yerel Kurulum

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env         # .env dosyasını kendi değerlerinizle doldurun

uvicorn app.main:app --reload
```

API varsayılan olarak `http://127.0.0.1:8000` üzerinde çalışır.
İnteraktif dokümantasyon: `http://127.0.0.1:8000/docs` (Swagger UI) veya `/redoc`.

## Kimlik Doğrulama Akışı

1. `POST /api/v1/auth/register` veya `POST /api/v1/auth/login` → `accessToken` + `refreshToken` döner.
2. Sonraki tüm isteklerde `Authorization: Bearer <accessToken>` header'ı gönderilir.
3. `accessToken` süresi dolduğunda `POST /api/v1/auth/refresh` ile (body: ham refresh token string'i)
   yeni bir `accessToken`/`refreshToken` çifti alınır.

Bu akış; hayvan profilleri, aşı/ilaç/veteriner/mama/su/egzersiz/kilo kayıtlarının
backend'e **yedeklenmesi** (senkronizasyon) içindir. Android istemcisi tüm bu
verileri zaten yerel Room veritabanında tutar ve giriş yapılmasa da tam
işlevsel çalışır (offline-first); giriş yalnızca isteğe bağlı bulut yedeğini
etkinleştirir.

## Yapay Zekâ Analizi

`POST /api/v1/analysis` uç noktası, multipart form-data ile bir `photo` dosyası ve `petId`
alanı bekler. Backend, fotoğrafı Groq'un görsel destekli modeline (`GROQ_MODEL`) gönderir
ve yapılandırılmış bir JSON yanıt (bulgular, veteriner/beslenme/hijyen önerileri) üretir.
`GROQ_API_KEY` tanımlı değilse veya Groq isteği başarısız olursa, kullanıcıyı her zaman
veterinere yönlendiren güvenli bir varsayılan yanıt döner (`services/ai_service.py`).

**Bu uç nokta bilinçli olarak hesap/giriş gerektirmez** — analiz sonucu Android
tarafında yerel veritabanına kaydedilir ve geçmiş oradan okunur; backend yalnızca
tek seferlik Groq çağrısı için kullanılır, `pet_id` de yalnızca kayıt amaçlı
bir referans olarak saklanır (backend'deki `pets` tablosuna bağlı değildir).
Kötüye kullanımı ve buna bağlı Groq maliyetini sınırlamak için basit, bellek
içi bir **IP başına günlük istek limiti** uygulanır
(`ANALYSIS_DAILY_LIMIT_PER_IP`, varsayılan: 5 — bkz. `services/rate_limiter.py`).
Limit aşıldığında `429 Too Many Requests` döner.

> **Düzeltilen hata:** Android istemcisi multipart form alanını `petId`
> (camelCase) olarak gönderiyor, ancak uç nokta `pet_id` (snake_case)
> bekliyordu — bu da her istekte `422 Unprocessable Entity` hatasına yol
> açıyordu (hesap/giriş şartından tamamen bağımsız bir hataydı). Parametreye
> `alias="petId"` eklenerek Android'i hiç değiştirmeden düzeltildi.

**Sonuç kesinlikle bir teşhis değildir**; her yanıt bunu belirten bir `disclaimer` alanı içerir.

## Render.com Üzerinde Dağıtım

`render.yaml`, bir web servisi + ücretsiz plan PostgreSQL veritabanı tanımlar:

1. Render Dashboard > New > Blueprint > bu repoyu seçin.
2. `SECRET_KEY` otomatik üretilir; `GROQ_API_KEY` gibi `sync: false` olarak işaretli
   değişkenleri Dashboard > Environment sekmesinden manuel girin.
3. Deploy sonrası health check: `GET /health`.

### Sorun giderme: "maturin failed" / "Read-only file system" / pydantic-core derleme hatası

Render, yeni servislerde varsayılan olarak en güncel Python sürümünü (örn. 3.14)
kullanır. `pydantic-core` gibi bazı bağımlılıkların bu kadar yeni bir sürüm için
henüz hazır (prebuilt) wheel dosyası olmayabilir; bu durumda pip paketi
kaynaktan (Rust/maturin ile) derlemeye çalışır ve Render'ın salt-okunur (read-only)
derleme ortamında bu derleme başarısız olur.

Bunu önlemek için `render.yaml` içinde `PYTHON_VERSION=3.12.7` sabitlenmiştir
(ayrıca `backend/.python-version` dosyası da yedek olarak eklenmiştir). Eğer
servisiniz Blueprint yerine elle (manuel "New Web Service" akışıyla) oluşturulduysa
`render.yaml` otomatik uygulanmaz; bu durumda:

1. Render Dashboard > servisiniz > **Environment** sekmesine gidin.
2. `PYTHON_VERSION` adında yeni bir değişken ekleyin, değeri `3.12.7` olsun.
3. **Manual Deploy > Clear build cache & deploy** ile yeniden dağıtın.

### Sorun giderme: `AppImportError: Failed to find attribute 'app' in 'app'`

Bu hata, servis Blueprint yerine elle oluşturulduğunda ortaya çıkar: Render,
`render.yaml`'daki `startCommand`'i okumaz ve kendi tahmini olan `gunicorn app:app`
komutunu kullanır — ama FastAPI uygulaması `app/main.py` içinde `app.main:app`
olarak tanımlıdır. Elle oluşturulmuş bir serviste **Settings > Build & Deploy**
altında şunları girin:

- **Root Directory:** `backend`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:**
  ```
  gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers 1 --timeout 60
  ```
  (Tek worker (`--workers 1`) kullanılır: SQLite eşzamanlı yazmayı iyi
  desteklemez ve birden fazla worker, açılışta tabloları aynı anda oluşturmaya
  çalışıp `table already exists` hatasına yol açabilir — bkz. aşağıdaki not.)

### ⚠️ Önemli: `DATABASE_URL` ayarlanmazsa veriler kaybolur

Servis Blueprint yerine elle oluşturulduysa, `render.yaml`'daki yönetilen
(managed) PostgreSQL veritabanı da otomatik oluşturulmaz — uygulama sessizce
yerel **SQLite** dosyasına (`sqlite:///./petmeta.db`) düşer. Render'ın ücretsiz
web servislerinde disk **kalıcı değildir**: her yeniden dağıtımda (redeploy)
veya servis yeniden başlatıldığında bu dosya **silinir** ve tüm
kullanıcılar/hayvanlar/kayıtlar kaybolur.

Gerçek/kalıcı veri için:

1. Render Dashboard > **New +** > **PostgreSQL** ile ücretsiz bir veritabanı oluşturun.
2. Oluşan veritabanının **Internal Connection String**'ini kopyalayın.
3. Backend servisinizin **Environment** sekmesine `DATABASE_URL` adında bir
   değişken ekleyip bu bağlantı dizesini yapıştırın.
4. **Manual Deploy > Clear build cache & deploy** ile yeniden dağıtın.

## Veritabanı Şeması

İlk sürümde tablolar `app.main` içindeki `startup` event'inde `Base.metadata.create_all()`
ile otomatik oluşturulur. Üretimde şema değişiklikleri için Alembic migration'larının
kullanılması önerilir (bu depoda hazır bir başlangıç noktası olarak `alembic` bağımlılığı
`requirements.txt` içine eklenmiştir).
