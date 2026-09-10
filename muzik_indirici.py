import os
import re
import sys
import threading
import queue
import json
import urllib.request

import customtkinter as ctk
import yt_dlp

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    SPOTIPY_VAR = True
except Exception:
    SPOTIPY_VAR = False

try:
    from spotify_scraper import SpotifyClient as _SpotifyScraper
    SCRAPER_VAR = True
except Exception:
    SCRAPER_VAR = False

# Spotify ozelligi ikisinden biriyle calisir
SPOTIFY_VAR = SPOTIPY_VAR or SCRAPER_VAR


# ============================================================
#   SURUM & GUNCELLEME AYARLARI
# ============================================================
SURUM = "1.3"

# --- BURAYI KENDI GITHUB BILGILERINLE DOLDUR ---
GH_KULLANICI = "MuammerGrG"           # github kullanici adin
GH_REPO = "music-downloader"          # repo adin
GH_BRANCH = "main"                    # genelde main
# ------------------------------------------------

def _ham_url(dosya):
    return (f"https://raw.githubusercontent.com/"
            f"{GH_KULLANICI}/{GH_REPO}/{GH_BRANCH}/{dosya}")


# ============================================================
#   AYAR KAYDETME (tema, sarki sayisi, dil)
# ============================================================
VARSAYILAN_AYAR = {"tema": "dark", "sarki_sayisi": 100, "dil": "tr",
                   "spotify_id": "", "spotify_secret": "",
                   "kalite": "320", "ulke": "TR"}


# ============================================================
#   DIL / CEVIRI
# ============================================================
METIN = {
    "tr": {
        "altbaslik": "Orijinal, MP3 320 kbps",
        "mod": "Mod:",
        "mod_sanatci": "Sanatçının en iyileri ({n})",
        "mod_parca": "Tek parça (şarkı adı)",
        "ipucu_genel": "Örn: Tarkan   veya   Tarkan Kuzu Kuzu",
        "ipucu_sanatci": "Örn: Tarkan   (en iyi {n} orijinal iner)",
        "ipucu_parca": "Örn: Tarkan Kuzu Kuzu   (tek şarkı)",
        "siraya_ekle": "＋ Sıraya Ekle",
        "indirme_sirasi": "İndirme Sırası",
        "temizle": "Temizle",
        "baslat": "▼  İNDİRMEYİ BAŞLAT",
        "indiriliyor": "İNDİRİLİYOR...",
        "durum": "Durum",
        "etiket_sanatci": "🎤 Sanatçı",
        "etiket_parca": "🎵 Parça",
        "ffmpeg_yok": "⚠ ffmpeg.exe bulunamadı — MP3 dönüşümü çalışmayabilir.",
        "once_ekle": "Önce sıraya en az bir şey ekle.",
        "hepsi_bitti": "\n✅ HEPSİ BİTTİ!\n📁 Konum: {yol}",
        "bildirim": "🔔  Güncelleme mevcut: v{v}  —  yüklemek için tıkla",
        # arama/log
        "log_sanatci": "\n♪ {ad} — en iyi {n} orijinal şarkı",
        "log_tamam": "   {n} şarkı tamamlandı.",
        "log_parca": "\n♪ '{q}' aranıyor (orijinal, en çok dinlenen)",
        "log_indirildi": "   ✓ indirildi: {ad}",
        "log_hata": "   ! hata: {e}",
        "arama_sanatci_ek": "şarkıları",
        # ayarlar
        "ayarlar": "⚙  Ayarlar",
        "yuklu_surum": "Yüklü sürüm:  v{v}",
        "yeni_var": "🔔 Yeni sürüm var: v{v}",
        "guncel_kullaniyorsun": "En güncel sürümü kullanıyorsun ✓",
        "indir_kur": "⬇  İndir ve Kur",
        "cekiliyor": "Güncelleme çekiliyor, bekle...",
        "indirildi_yeniden": "✓ İndirildi — yeniden başlat",
        "tekrar_dene": "Tekrar dene",
        "denetle": "Güncellemeleri Denetle",
        "kontrol_ediliyor": "Kontrol ediliyor...",
        "tema_lbl": "Tema:",
        "tema_koyu": "Koyu", "tema_acik": "Açık", "tema_sistem": "Sistem",
        "sarki_lbl": "Sanatçı başına şarkı:",
        "sarki_aralik": "10 – 200 arası",
        "dil_lbl": "Dil / Language:",
        "konum_lbl": "İndirme konumu:",
        "klasoru_ac": "📁 Klasörü Aç",
        # spotify
        "mod_spotify": "🎧 Spotify listesi",
        "ipucu_spotify": "Spotify playlist/albüm linkini yapıştır",
        "spotify_baslik": "Spotify API (isteğe bağlı — daha güvenilir)",
        "spotify_id_ph": "Client ID",
        "spotify_secret_ph": "Client Secret",
        "spotify_nasil": "Boş bırakabilirsin; link doğrudan da okunmaya çalışılır",
        "spotify_okunuyor": "\n🎧 Spotify listesi okunuyor...",
        "spotify_bulundu": "   {n} şarkı bulundu, sıraya eklendi.",
        "spotify_hata": "   ! Spotify: {e}",
        "spotify_yok": "spotipy kurulu değil — Spotify özelliği devre dışı.",
        "etiket_spotify": "🎧 Spotify",
        # youtube top + kalite
        "mod_yttop": "📈 YouTube Top 50",
        "ipucu_yttop": "Aşağıdaki '▼ İNDİRMEYİ BAŞLAT' ile ülkenin Top 50'sini indir",
        "yttop_ekle": "📈 YouTube Top 50 → Sıraya Ekle",
        "yt_top_okunuyor": "\n📈 YouTube Top 50 ({ulke}) indiriliyor...",
        "etiket_yttop": "📈 YT Top",
        "kalite_lbl": "Ses kalitesi:",
        "ulke_lbl": "YouTube Top ülkesi:",
    },
    "en": {
        "altbaslik": "Originals only, MP3 320 kbps",
        "mod": "Mode:",
        "mod_sanatci": "Artist's top tracks ({n})",
        "mod_parca": "Single track (song name)",
        "ipucu_genel": "e.g. Tarkan   or   Tarkan Kuzu Kuzu",
        "ipucu_sanatci": "e.g. Tarkan   (downloads top {n} originals)",
        "ipucu_parca": "e.g. Tarkan Kuzu Kuzu   (single song)",
        "siraya_ekle": "＋ Add to Queue",
        "indirme_sirasi": "Download Queue",
        "temizle": "Clear",
        "baslat": "▼  START DOWNLOAD",
        "indiriliyor": "DOWNLOADING...",
        "durum": "Status",
        "etiket_sanatci": "🎤 Artist",
        "etiket_parca": "🎵 Track",
        "ffmpeg_yok": "⚠ ffmpeg.exe not found — MP3 conversion may not work.",
        "once_ekle": "Add at least one item to the queue first.",
        "hepsi_bitti": "\n✅ ALL DONE!\n📁 Location: {yol}",
        "bildirim": "🔔  Update available: v{v}  —  click to install",
        "log_sanatci": "\n♪ {ad} — top {n} original tracks",
        "log_tamam": "   {n} tracks completed.",
        "log_parca": "\n♪ Searching '{q}' (original, most played)",
        "log_indirildi": "   ✓ downloaded: {ad}",
        "log_hata": "   ! error: {e}",
        "arama_sanatci_ek": "songs",
        "ayarlar": "⚙  Settings",
        "yuklu_surum": "Installed version:  v{v}",
        "yeni_var": "🔔 New version available: v{v}",
        "guncel_kullaniyorsun": "You're on the latest version ✓",
        "indir_kur": "⬇  Download & Install",
        "cekiliyor": "Fetching update, please wait...",
        "indirildi_yeniden": "✓ Downloaded — restart the app",
        "tekrar_dene": "Try again",
        "denetle": "Check for Updates",
        "kontrol_ediliyor": "Checking...",
        "tema_lbl": "Theme:",
        "tema_koyu": "Dark", "tema_acik": "Light", "tema_sistem": "System",
        "sarki_lbl": "Songs per artist:",
        "sarki_aralik": "between 10 – 200",
        "dil_lbl": "Language / Dil:",
        "konum_lbl": "Download location:",
        "klasoru_ac": "📁 Open Folder",
        # spotify
        "mod_spotify": "🎧 Spotify list",
        "ipucu_spotify": "Paste a Spotify playlist/album link",
        "spotify_baslik": "Spotify API (optional — more reliable)",
        "spotify_id_ph": "Client ID",
        "spotify_secret_ph": "Client Secret",
        "spotify_nasil": "Can be left empty; the link is tried directly too",
        "spotify_okunuyor": "\n🎧 Reading Spotify list...",
        "spotify_bulundu": "   {n} tracks found, added to queue.",
        "spotify_hata": "   ! Spotify: {e}",
        "spotify_yok": "spotipy not installed — Spotify feature disabled.",
        "etiket_spotify": "🎧 Spotify",
        # youtube top + kalite
        "mod_yttop": "📈 YouTube Top 50",
        "ipucu_yttop": "Use '▼ START DOWNLOAD' below to grab the country's Top 50",
        "yttop_ekle": "📈 YouTube Top 50 → Add to Queue",
        "yt_top_okunuyor": "\n📈 Downloading YouTube Top 50 ({ulke})...",
        "etiket_yttop": "📈 YT Top",
        "kalite_lbl": "Audio quality:",
        "ulke_lbl": "YouTube Top country:",
    },
}

_AKTIF_DIL = "tr"

def T(anahtar, **kw):
    s = METIN.get(_AKTIF_DIL, METIN["tr"]).get(anahtar, anahtar)
    return s.format(**kw) if kw else s


def _ayar_yolu():
    if getattr(sys, 'frozen', False):
        temel = os.path.dirname(sys.executable)
    else:
        temel = os.path.dirname(os.path.abspath(__file__))
    # exe klasoru yazilamazsa kullanici klasorune dus
    try:
        test = os.path.join(temel, ".yazma_testi")
        with open(test, "w") as f:
            f.write("x")
        os.remove(test)
    except Exception:
        temel = os.path.join(os.path.expanduser("~"), ".muzikindirici")
        os.makedirs(temel, exist_ok=True)
    return os.path.join(temel, "ayarlar.json")


def ayar_yukle():
    try:
        with open(_ayar_yolu(), "r", encoding="utf-8") as f:
            d = json.load(f)
        ayar = dict(VARSAYILAN_AYAR)
        ayar.update({k: v for k, v in d.items() if k in VARSAYILAN_AYAR})
        return ayar
    except Exception:
        return dict(VARSAYILAN_AYAR)


def ayar_kaydet(ayar):
    try:
        with open(_ayar_yolu(), "w", encoding="utf-8") as f:
            json.dump(ayar, f)
        return True
    except Exception:
        return False


def guncelleme_kontrol():
    """GitHub'daki version.txt'yi okur. (uzak_surum, yeni_var_mi) doner.
    Hata olursa (None, False)."""
    try:
        url = _ham_url("version.txt")
        with urllib.request.urlopen(url, timeout=6) as r:
            uzak = r.read().decode("utf-8").strip()
        return uzak, _surum_yeni_mi(uzak, SURUM)
    except Exception:
        return None, False


def _surum_yeni_mi(uzak, yerel):
    """1.2 > 1.1 gibi sayisal karsilastirma."""
    def parcala(s):
        return [int(x) for x in re.findall(r'\d+', s)]
    try:
        return parcala(uzak) > parcala(yerel)
    except Exception:
        return uzak != yerel


def veri_klasoru():
    """Yazilabilir kalici klasor (guncel kod, ayarlar burada).
    Program Files yazilamaz oldugu icin kullanici klasorunu kullaniriz."""
    yol = os.path.join(os.path.expanduser("~"), ".muzikindirici")
    try:
        os.makedirs(yol, exist_ok=True)
    except Exception:
        yol = os.path.expanduser("~")
    return yol


def _spotify_scraper_oku(link):
    """API'siz: spotifyscraper ile public playlist/album okur."""
    if not SCRAPER_VAR:
        return None, "scraper yok"
    try:
        c = _SpotifyScraper()
        if "album" in link:
            info = c.get_album(link)
        else:
            info = c.get_playlist(link)
        parcalar = info.get("tracks") or []
        sarkilar = []
        for tr in parcalar:
            ad = tr.get("name")
            if not ad:
                continue
            sanatcilar = tr.get("artists") or []
            sanatci = sanatcilar[0].get("name") if sanatcilar else ""
            sarkilar.append(f"{sanatci} - {ad}".strip(" -"))
        try:
            c.close()
        except Exception:
            pass
        if sarkilar:
            return sarkilar, None
        return None, "bos"
    except Exception as e:
        return None, str(e)


def _spotify_api_oku(link, client_id, client_secret):
    """API'li: spotipy ile okur (anahtar gerekir)."""
    if not SPOTIPY_VAR:
        return [], "spotipy kurulu değil."
    if not client_id or not client_secret:
        return [], "Spotify API bilgileri girilmemiş (Ayarlar)."
    m = re.search(r'(playlist|album)/([A-Za-z0-9]+)', link)
    if not m:
        return [], "Geçerli bir Spotify playlist/albüm linki değil."
    tur, kimlik = m.group(1), m.group(2)
    try:
        yetki = SpotifyClientCredentials(client_id=client_id,
                                         client_secret=client_secret)
        sp = spotipy.Spotify(client_credentials_manager=yetki)
        sarkilar = []
        if tur == "playlist":
            sonuc = sp.playlist_items(kimlik, additional_types=["track"])
        else:
            sonuc = sp.album_tracks(kimlik)
        while sonuc:
            for oge in sonuc["items"]:
                tr = oge.get("track") if tur == "playlist" else oge
                if tr and tr.get("name"):
                    sanatci = tr["artists"][0]["name"] if tr.get("artists") else ""
                    sarkilar.append(f"{sanatci} - {tr['name']}".strip(" -"))
            sonuc = sp.next(sonuc) if sonuc.get("next") else None
        if not sarkilar:
            return [], "Listede şarkı bulunamadı (özel liste olabilir)."
        return sarkilar, None
    except Exception as e:
        mesaj = str(e)
        if "invalid_client" in mesaj.lower() or "400" in mesaj:
            return [], "Spotify API bilgileri hatalı görünüyor (Ayarlar)."
        return [], f"Spotify hatası: {mesaj}"


def spotify_playlist_oku(link, client_id="", client_secret=""):
    """Spotify playlist/album okur. Once API'siz dener, olmazsa API'ye duser.
    Doner: (liste, hata_mesaji)."""
    if not re.search(r'(playlist|album)/[A-Za-z0-9]+', link):
        return [], "Geçerli bir Spotify playlist/albüm linki değil."

    # 1) API'siz (anahtar gerektirmez)
    if SCRAPER_VAR:
        sarkilar, hata = _spotify_scraper_oku(link)
        if sarkilar:
            return sarkilar, None
        # API'siz basarisiz; anahtar varsa API'ye dus
        if not (SPOTIPY_VAR and client_id and client_secret):
            # anahtar yoksa API'siz hatayi kullanici dostu ver
            return [], "Liste okunamadı (API anahtarı girersen daha güvenilir olur)."

    # 2) API'li (anahtar varsa)
    return _spotify_api_oku(link, client_id, client_secret)


def guncellemeyi_indir():
    """Guncel muzik_indirici.py'yi cekip yazilabilir veri klasorune kaydeder."""
    try:
        kod_url = _ham_url("muzik_indirici.py")
        with urllib.request.urlopen(kod_url, timeout=15) as r:
            yeni_kod = r.read().decode("utf-8")
        if len(yeni_kod) < 500 or "customtkinter" not in yeni_kod:
            return False, "İndirilen dosya geçersiz görünüyor."
        hedef = os.path.join(veri_klasoru(), "guncel_muzik_indirici.py")
        with open(hedef, "w", encoding="utf-8") as f:
            f.write(yeni_kod)
        return True, "Güncelleme indirildi. Uygulamayı kapatıp açın."
    except Exception as e:
        return False, f"İndirme hatası: {e}"


# ============================================================
#   YARDIMCI: yol bulma (exe / script uyumlu)
# ============================================================
def kaynak_yolu(dosya):
    """PyInstaller gomulu dosyalari _MEIPASS'ta acar."""
    if getattr(sys, 'frozen', False):
        temel = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        temel = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(temel, dosya)


def uygulama_klasoru():
    """Ciktilarin (music) kaydedilecegi kalici, yazilabilir klasor.
    Program Files'a kurulunca oraya yazamayiz; kullanicinin Muzik
    klasorune 'MuzikIndirici' altina kaydediyoruz."""
    if getattr(sys, 'frozen', False):
        # Windows'ta Muzik klasoru
        muzik = os.path.join(os.path.expanduser("~"), "Music")
        if not os.path.isdir(muzik):
            muzik = os.path.expanduser("~")
        hedef = os.path.join(muzik, "MuzikIndirici")
        os.makedirs(hedef, exist_ok=True)
        return hedef
    return os.path.dirname(os.path.abspath(__file__))


def ffmpeg_bul():
    adaylar = [kaynak_yolu("ffmpeg.exe")]
    if getattr(sys, 'frozen', False):
        adaylar.append(os.path.join(os.path.dirname(sys.executable), "ffmpeg.exe"))
    else:
        adaylar.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg.exe"))
    for aday in adaylar:
        if os.path.exists(aday):
            return aday
    return None


# ============================================================
#   FILTRELER
# ============================================================
ISTENMEYEN = [
    r'\blive\b', r'\bcanli\b', r'\bremix\b', r'\bcover\b', r'\bkaraoke\b',
    r'\bakustik\b', r'\bacoustic\b', r'\bsped\s*up\b', r'\bslowed\b',
    r'\breverb\b', r'\b8d\b', r'\bnightcore\b', r'\bperformance\b',
    r'\bkonser\b', r'\bteaser\b', r'\bsnippet\b', r'\bmashup\b',
    r'\binstrumental\b', r'\bbeat\b', r'\bedit\b', r'\bmix\b',
    r'\b1\s*saat\b', r'\b1\s*hour\b', r'\b10\s*saat\b', r'\b10\s*hour\b',
    r'\bsaatlik\b', r'\bhour\s*loop\b', r'\bloop\b', r'\bkesintisiz\b',
    r'\bnonstop\b', r'\bnon\s*stop\b', r'\bbir\s*saat\b',
    r'\balbum\b', r'\balbumu\b', r'\bfull\s*album\b', r'\bderleme\b',
    r'\bmegamix\b', r'\bset\b', r'\bdj\s*set\b', r'\ball\s*songs\b',
    r'\btum\s*sarkilari\b', r'\bgreatest\s*hits\b', r'\bplaylist\b',
    r'\bmix\s*\d+', r'\btop\s*\d+\b', r'\bcompilation\b', r'\bbest\s*of\b',
]

COP_KALIPLAR = [
    r'\(official\s*(music\s*)?video\)', r'\[official\s*(music\s*)?video\]',
    r'\(official\s*(lyric|lyrics)\s*video\)', r'\[official\s*(lyric|lyrics)\s*video\]',
    r'\(official\s*audio\)', r'\[official\s*audio\]', r'\(official\s*visualizer\)',
    r'\(lyric\s*video\)', r'\(lyrics\)', r'\(visualizer\)', r'\(audio\)',
    r'\(video\)', r'\(prod[^)]*\)', r'official\s*music\s*video',
    r'official\s*video', r'official\s*audio', r'lyric\s*video', r'visualizer',
    r'\b4k\b', r'\bhd\b', r'\bmv\b', r'\bfull\s*hd\b', r'#\w+', r'@\w+',
    r'\bofficial\b', r'\bmusic\b\s*\bvideo\b',
]


def sarki_anahtari(baslik):
    s = baslik.lower()
    s = re.sub(r'\(.*?\)|\[.*?\]', ' ', s)
    s = re.sub(r'feat\.?|ft\.?', ' ', s)
    s = re.sub(r'official|video|music|lyric[s]?|audio|visualizer', ' ', s)
    s = re.sub(r'[^a-z0-9ğüşıöç ]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s.replace(' ', '')


def filtre_yap(gorulen_set):
    MAX_SANIYE = 10 * 60
    MIN_SANIYE = 60

    def _filtre(info):
        baslik = info.get('title', '') or ''
        d = baslik.lower()
        for kalip in ISTENMEYEN:
            if re.search(kalip, d):
                return f"atlandi (versiyon): {baslik}"
        sure = info.get('duration')
        if sure:
            if sure > MAX_SANIYE:
                return f"atlandi (uzun/album): {baslik}"
            if sure < MIN_SANIYE:
                return f"atlandi (kisa): {baslik}"
        anahtar = sarki_anahtari(baslik)
        if anahtar and anahtar in gorulen_set:
            return f"atlandi (mukerrer): {baslik}"
        if anahtar:
            gorulen_set.add(anahtar)
        return None
    return _filtre


def isim_temizle(ad):
    kok, uzanti = os.path.splitext(ad)
    kok = kok.replace('_', ' ')
    for kalip in COP_KALIPLAR:
        kok = re.sub(kalip, '', kok, flags=re.IGNORECASE)
    kok = re.sub(r'\s+', ' ', kok).strip()
    kok = kok.strip(' -–—._')
    kok = re.sub(r'\s+', ' ', kok).strip()
    return (kok or "adsiz") + uzanti


def klasoru_temizle(kok_klasor, log):
    if not os.path.isdir(kok_klasor):
        return
    for dizin, _, dosyalar in os.walk(kok_klasor):
        for dosya in dosyalar:
            if not dosya.lower().endswith('.mp3'):
                continue
            yeni = isim_temizle(dosya)
            if yeni == dosya:
                continue
            eski_yol = os.path.join(dizin, dosya)
            yeni_yol = os.path.join(dizin, yeni)
            if os.path.exists(yeni_yol) and eski_yol.lower() != yeni_yol.lower():
                temel, uz = os.path.splitext(yeni)
                i = 2
                while os.path.exists(os.path.join(dizin, f"{temel} ({i}){uz}")):
                    i += 1
                yeni_yol = os.path.join(dizin, f"{temel} ({i}){uz}")
            try:
                os.rename(eski_yol, yeni_yol)
            except Exception:
                pass


# ============================================================
#   INDIRME MOTORU
# ============================================================
class Indirici:
    def __init__(self, log_fn, ilerleme_fn, kalite="320"):
        self.log = log_fn
        self.ilerleme = ilerleme_fn
        self.ffmpeg = ffmpeg_bul()
        self.iptal = False
        self.kalite = kalite

    def _ydl_opts(self, hedef_klasor, gorulen, max_indir):
        opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': self.kalite,
            }],
            'outtmpl': os.path.join(hedef_klasor, '%(title)s.%(ext)s'),
            'ignoreerrors': True,
            'restrictfilenames': True,
            'windowsfilenames': True,
            'noplaylist': True,
            'match_filter': filtre_yap(gorulen),
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [self._hook],
        }
        if max_indir:
            opts['max_downloads'] = max_indir
        if self.ffmpeg:
            opts['ffmpeg_location'] = self.ffmpeg
        return opts

    def _hook(self, d):
        if self.iptal:
            raise Exception("iptal")
        if d['status'] == 'finished':
            ad = os.path.basename(d.get('filename', ''))
            self.log(T("log_indirildi", ad=ad))

    def sanatci_indir(self, sanatci, adet=100):
        sanatci = sanatci.strip()
        if not sanatci:
            return
        music_kok = os.path.join(uygulama_klasoru(), "music")
        hedef = os.path.join(music_kok, sanatci)
        os.makedirs(hedef, exist_ok=True)
        gorulen = set()
        self.log(T("log_sanatci", ad=sanatci.upper(), n=adet))
        arama = f"ytsearch{adet * 2}:{sanatci} {T('arama_sanatci_ek')}"
        opts = self._ydl_opts(hedef, gorulen, adet)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([arama])
        except yt_dlp.utils.MaxDownloadsReached:
            self.log(T("log_tamam", n=adet))
        except Exception as e:
            self.log(T("log_hata", e=e))
        klasoru_temizle(hedef, self.log)

    def parca_indir(self, sorgu):
        sorgu = sorgu.strip()
        if not sorgu:
            return
        music_kok = os.path.join(uygulama_klasoru(), "music")
        hedef = os.path.join(music_kok, "Parcalar")
        os.makedirs(hedef, exist_ok=True)
        gorulen = set()
        self.log(T("log_parca", q=sorgu))
        # 5 aday tara, filtreden gecen ILK 1 orijinali indir
        arama = f"ytsearch5:{sorgu}"
        opts = self._ydl_opts(hedef, gorulen, 1)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([arama])
        except yt_dlp.utils.MaxDownloadsReached:
            pass
        except Exception as e:
            self.log(T("log_hata", e=e))
        klasoru_temizle(hedef, self.log)

    def youtube_top_indir(self, ulke, adet=50):
        """YouTube'un ulke bazli populer muzik listesini indirir."""
        music_kok = os.path.join(uygulama_klasoru(), "music")
        hedef = os.path.join(music_kok, f"YouTube_Top_{ulke}")
        os.makedirs(hedef, exist_ok=True)
        gorulen = set()
        self.log(T("yt_top_okunuyor", ulke=ulke))
        # YouTube'un resmi "music charts" playlisti ulke bazli
        # Once populer muzik aramasi ile dene (en saglam yontem)
        arama = f"ytsearch{adet * 2}:top {ulke} songs this week"
        opts = self._ydl_opts(hedef, gorulen, adet)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([arama])
        except yt_dlp.utils.MaxDownloadsReached:
            self.log(T("log_tamam", n=adet))
        except Exception as e:
            self.log(T("log_hata", e=e))
        klasoru_temizle(hedef, self.log)


# ============================================================
#   ARAYUZ
# ============================================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class Uygulama(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Kayitli ayarlari yukle ve uygula
        self.ayar = ayar_yukle()
        ctk.set_appearance_mode(self.ayar.get("tema", "dark"))
        global _AKTIF_DIL
        _AKTIF_DIL = self.ayar.get("dil", "tr")

        self.title("Müzik İndirici")
        self.geometry("640x680")
        self.minsize(560, 600)

        try:
            self.iconbitmap(kaynak_yolu("logo.ico"))
        except Exception:
            pass

        self.mesaj_kuyrugu = queue.Queue()
        self.calisiyor = False
        self.indirici = None

        self._arayuz_kur()
        self.after(100, self._kuyrugu_isle)
        self.uzak_surum = None
        # Acilista arka planda guncelleme kontrol et
        threading.Thread(target=self._guncelleme_kontrol_arka, daemon=True).start()

    def _arayuz_kur(self):
        # Guncelleme bildirim seridi (baslangicta gizli)
        self.bildirim_serit = ctk.CTkFrame(self, fg_color="#2b5c2b", height=36)
        self.bildirim_btn = ctk.CTkButton(
            self.bildirim_serit, text="", fg_color="transparent",
            hover_color="#347a34", anchor="w",
            command=self._ayarlari_ac)
        self.bildirim_btn.pack(fill="both", expand=True, padx=8, pady=2)
        # pack edilmedi; guncelleme bulununca gosterilecek

        # Baslik satiri (sag ust ayarlar dislisi)
        ust = ctk.CTkFrame(self, fg_color="transparent")
        self._ust_cerceve = ust
        ust.pack(fill="x", padx=20, pady=(18, 6))
        sol = ctk.CTkFrame(ust, fg_color="transparent")
        sol.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(sol, text="🎼  Müzik İndirici",
                     font=ctk.CTkFont(size=26, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(sol, text=f"{T('altbaslik')}   ·   v{SURUM}",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w")
        ctk.CTkButton(ust, text="⚙", width=40, height=40,
                      font=ctk.CTkFont(size=18),
                      fg_color="gray25", hover_color="gray35",
                      command=self._ayarlari_ac).pack(side="right", anchor="n")

        # Mod secimi
        self.mod = ctk.StringVar(value="sanatci")
        mod_cerceve = ctk.CTkFrame(self)
        mod_cerceve.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(mod_cerceve, text=T("mod"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(12, 8), pady=10)
        self.sanatci_radio = ctk.CTkRadioButton(
            mod_cerceve, text=T("mod_sanatci", n=self.ayar.get('sarki_sayisi', 100)),
            variable=self.mod, value="sanatci",
            command=self._mod_degisti)
        self.sanatci_radio.pack(side="left", padx=8, pady=10)
        ctk.CTkRadioButton(mod_cerceve, text=T("mod_parca"),
                           variable=self.mod, value="parca",
                           command=self._mod_degisti).pack(side="left", padx=8, pady=10)
        if SPOTIFY_VAR:
            ctk.CTkRadioButton(mod_cerceve, text=T("mod_spotify"),
                               variable=self.mod, value="spotify",
                               command=self._mod_degisti).pack(side="left", padx=8, pady=10)
        ctk.CTkRadioButton(mod_cerceve, text=T("mod_yttop"),
                           variable=self.mod, value="yttop",
                           command=self._mod_degisti).pack(side="left", padx=8, pady=10)

        # Giris + ekle
        giris_cerceve = ctk.CTkFrame(self, fg_color="transparent")
        giris_cerceve.pack(fill="x", padx=20, pady=(0, 6))
        self.giris = ctk.CTkEntry(giris_cerceve,
                                  placeholder_text=T("ipucu_genel"),
                                  height=40, font=ctk.CTkFont(size=14))
        self.giris.pack(side="left", fill="x", expand=True)
        self.giris.bind("<Return>", lambda e: self._siraya_ekle())
        ctk.CTkButton(giris_cerceve, text=T("siraya_ekle"), width=130, height=40,
                      command=self._siraya_ekle).pack(side="left", padx=(8, 0))

        # Sira (kuyruk)
        sira_ust = ctk.CTkFrame(self, fg_color="transparent")
        sira_ust.pack(fill="x", padx=20, pady=(8, 0))
        ctk.CTkLabel(sira_ust, text=T("indirme_sirasi"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        ctk.CTkButton(sira_ust, text=T("temizle"), width=70, height=26,
                      fg_color="gray30", hover_color="gray20",
                      command=self._sirayi_temizle).pack(side="right")

        self.sira_kutu = ctk.CTkTextbox(self, height=90, font=ctk.CTkFont(size=13))
        self.sira_kutu.pack(fill="x", padx=20, pady=(4, 8))
        self.sira_kutu.configure(state="disabled")
        self.sira_listesi = []

        # Baslat butonu
        self.baslat_btn = ctk.CTkButton(self, text=T("baslat"),
                                        height=46, font=ctk.CTkFont(size=16, weight="bold"),
                                        command=self._baslat)
        self.baslat_btn.pack(fill="x", padx=20, pady=6)

        # Ilerleme
        self.ilerleme_bar = ctk.CTkProgressBar(self)
        self.ilerleme_bar.pack(fill="x", padx=20, pady=(4, 2))
        self.ilerleme_bar.set(0)

        # Log
        ctk.CTkLabel(self, text=T("durum"),
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(6, 0))
        self.log_kutu = ctk.CTkTextbox(self, font=ctk.CTkFont(size=12), wrap="word")
        self.log_kutu.pack(fill="both", expand=True, padx=20, pady=(2, 16))
        self.log_kutu.configure(state="disabled")

        if not ffmpeg_bul():
            self._log(T("ffmpeg_yok"))
        if not SPOTIFY_VAR:
            self._log(T("spotify_yok"))

    def _mod_degisti(self):
        n = self.ayar.get('sarki_sayisi', 100)
        if self.mod.get() == "sanatci":
            self.giris.configure(placeholder_text=T("ipucu_sanatci", n=n))
        elif self.mod.get() == "spotify":
            self.giris.configure(placeholder_text=T("ipucu_spotify"))
        elif self.mod.get() == "yttop":
            self.giris.configure(placeholder_text=T("ipucu_yttop"))
        else:
            self.giris.configure(placeholder_text=T("ipucu_parca"))

    def _siraya_ekle(self):
        mod = self.mod.get()
        metin = self.giris.get().strip()
        # yttop disindaki modlar giris ister
        if not metin and mod != "yttop":
            return
        if mod == "yttop":
            # Giris gerektirmez, ulke ayardan gelir
            ulke = self.ayar.get("ulke", "TR")
            self.sira_listesi.append(("yttop", ulke))
            self.giris.delete(0, "end")
            self._sirayi_ciz()
            return
        if mod == "spotify":
            # Spotify linkini arka planda oku, sarkilari parca olarak ekle
            self.giris.delete(0, "end")
            self._log(T("spotify_okunuyor"))
            link = metin
            def isle():
                sarkilar, hata = spotify_playlist_oku(
                    link,
                    self.ayar.get("spotify_id", ""),
                    self.ayar.get("spotify_secret", ""))
                def bitir():
                    if hata:
                        self._log(T("spotify_hata", e=hata))
                    else:
                        for s in sarkilar:
                            self.sira_listesi.append(("parca", s))
                        self._log(T("spotify_bulundu", n=len(sarkilar)))
                        self._sirayi_ciz()
                self.after(0, bitir)
            threading.Thread(target=isle, daemon=True).start()
            return
        # Sanatci / parca: virgulle birden fazla
        for parca in metin.split(','):
            parca = parca.strip()
            if parca:
                self.sira_listesi.append((mod, parca))
        self.giris.delete(0, "end")
        self._sirayi_ciz()

    def _sirayi_ciz(self):
        self.sira_kutu.configure(state="normal")
        self.sira_kutu.delete("1.0", "end")
        for i, (mod, deger) in enumerate(self.sira_listesi, 1):
            if mod == "sanatci":
                etiket = T("etiket_sanatci")
            elif mod == "yttop":
                etiket = T("etiket_yttop")
            else:
                etiket = T("etiket_parca")
            self.sira_kutu.insert("end", f"{i}. [{etiket}]  {deger}\n")
        self.sira_kutu.configure(state="disabled")

    def _sirayi_temizle(self):
        if self.calisiyor:
            return
        self.sira_listesi.clear()
        self._sirayi_ciz()

    def _log(self, mesaj):
        self.log_kutu.configure(state="normal")
        self.log_kutu.insert("end", mesaj + "\n")
        self.log_kutu.see("end")
        self.log_kutu.configure(state="disabled")

    def _kuyrugu_isle(self):
        try:
            while True:
                tur, veri = self.mesaj_kuyrugu.get_nowait()
                if tur == "log":
                    self._log(veri)
                elif tur == "ilerleme":
                    self.ilerleme_bar.set(veri)
                elif tur == "bitti":
                    self._bitti()
                elif tur == "guncelleme":
                    self._bildirimi_goster(veri)
        except queue.Empty:
            pass
        self.after(100, self._kuyrugu_isle)

    def _baslat(self):
        if self.calisiyor:
            return
        # Girise yazip eklemeyi unutma ihtimaline karsi
        if self.giris.get().strip():
            self._siraya_ekle()
        if not self.sira_listesi:
            self._log(T("once_ekle"))
            return
        self.calisiyor = True
        self.baslat_btn.configure(state="disabled", text=T("indiriliyor"))
        gorevler = list(self.sira_listesi)
        threading.Thread(target=self._calis, args=(gorevler,), daemon=True).start()

    def _calis(self, gorevler):
        def log(m): self.mesaj_kuyrugu.put(("log", m))
        def ilerleme(v): self.mesaj_kuyrugu.put(("ilerleme", v))

        ind = Indirici(log, ilerleme, kalite=self.ayar.get("kalite", "320"))
        toplam = len(gorevler)
        for i, (mod, deger) in enumerate(gorevler):
            ilerleme(i / toplam)
            if mod == "sanatci":
                ind.sanatci_indir(deger, self.ayar.get("sarki_sayisi", 100))
            elif mod == "yttop":
                ind.youtube_top_indir(deger, 50)
            else:
                ind.parca_indir(deger)
        ilerleme(1.0)
        kayit_yeri = os.path.join(uygulama_klasoru(), "music")
        log(T("hepsi_bitti", yol=kayit_yeri))
        self.mesaj_kuyrugu.put(("bitti", None))

    def _guncelleme_kontrol_arka(self):
        uzak, yeni_var = guncelleme_kontrol()
        if yeni_var:
            self.uzak_surum = uzak
            self.mesaj_kuyrugu.put(("guncelleme", uzak))

    def _bildirimi_goster(self, uzak):
        self.bildirim_btn.configure(text=T("bildirim", v=uzak))
        self.bildirim_serit.pack(fill="x", side="top", before=self._ust_cerceve)

    def _ayarlari_ac(self):
        pencere = ctk.CTkToplevel(self)
        pencere.title(T("ayarlar").replace("⚙  ", ""))
        pencere.geometry("470x900")
        pencere.transient(self)
        try:
            pencere.after(200, lambda: pencere.iconbitmap(kaynak_yolu("logo.ico")))
        except Exception:
            pass

        ctk.CTkLabel(pencere, text=T("ayarlar"),
                     font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(18, 10))

        # Surum bilgisi
        kutu = ctk.CTkFrame(pencere)
        kutu.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(kutu, text=T("yuklu_surum", v=SURUM),
                     font=ctk.CTkFont(size=14)).pack(anchor="w", padx=14, pady=(12, 2))

        if self.uzak_surum and _surum_yeni_mi(self.uzak_surum, SURUM):
            durum = ctk.CTkLabel(kutu, text=T("yeni_var", v=self.uzak_surum),
                                 font=ctk.CTkFont(size=14, weight="bold"),
                                 text_color="#4caf50")
            durum.pack(anchor="w", padx=14, pady=2)

            ilerleme_lbl = ctk.CTkLabel(kutu, text="", font=ctk.CTkFont(size=12),
                                        text_color="gray")
            ilerleme_lbl.pack(anchor="w", padx=14, pady=(4, 2))

            def indir():
                indir_btn.configure(state="disabled", text=T("cekiliyor").replace("...", ""))
                ilerleme_lbl.configure(text=T("cekiliyor"))
                def isle():
                    ok, mesaj = guncellemeyi_indir()
                    def bitir():
                        ilerleme_lbl.configure(
                            text=mesaj,
                            text_color="#4caf50" if ok else "#e05555")
                        if ok:
                            indir_btn.configure(text=T("indirildi_yeniden"))
                        else:
                            indir_btn.configure(state="normal", text=T("tekrar_dene"))
                    self.after(0, bitir)
                threading.Thread(target=isle, daemon=True).start()

            indir_btn = ctk.CTkButton(kutu, text=T("indir_kur"), command=indir)
            indir_btn.pack(anchor="w", padx=14, pady=(6, 14))
        else:
            ctk.CTkLabel(kutu, text=T("guncel_kullaniyorsun"),
                         font=ctk.CTkFont(size=13), text_color="gray").pack(anchor="w", padx=14, pady=(2, 12))

            def tekrar_kontrol():
                kontrol_btn.configure(state="disabled", text=T("kontrol_ediliyor"))
                def isle():
                    uzak, yeni = guncelleme_kontrol()
                    def bitir():
                        kontrol_btn.configure(state="normal", text=T("denetle"))
                        if yeni:
                            self.uzak_surum = uzak
                            pencere.destroy()
                            self._bildirimi_goster(uzak)
                            self._ayarlari_ac()
                    self.after(0, bitir)
                threading.Thread(target=isle, daemon=True).start()

            kontrol_btn = ctk.CTkButton(kutu, text=T("denetle"),
                                        command=tekrar_kontrol)
            kontrol_btn.pack(anchor="w", padx=14, pady=(0, 14))

        # --- Tercihler: dil + tema + sarki sayisi ---
        tercih = ctk.CTkFrame(pencere)
        tercih.pack(fill="x", padx=20, pady=8)

        # Dil
        dil_satir = ctk.CTkFrame(tercih, fg_color="transparent")
        dil_satir.pack(fill="x", padx=14, pady=(12, 6))
        ctk.CTkLabel(dil_satir, text=T("dil_lbl"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        def dil_degistir(secim):
            global _AKTIF_DIL
            yeni = "tr" if secim.startswith("Türkçe") else "en"
            if yeni == _AKTIF_DIL:
                return
            _AKTIF_DIL = yeni
            self.ayar["dil"] = yeni
            ayar_kaydet(self.ayar)
            # Arayuzu yeniden kur
            pencere.destroy()
            self._arayuzu_yenile()

        dil_menu = ctk.CTkOptionMenu(dil_satir, values=["Türkçe", "English"],
                                     width=120, command=dil_degistir)
        dil_menu.set("Türkçe" if _AKTIF_DIL == "tr" else "English")
        dil_menu.pack(side="right")

        # Tema
        tema_satir = ctk.CTkFrame(tercih, fg_color="transparent")
        tema_satir.pack(fill="x", padx=14, pady=(6, 6))
        ctk.CTkLabel(tema_satir, text=T("tema_lbl"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        tema_secenek = [T("tema_koyu"), T("tema_acik"), T("tema_sistem")]
        tema_kod = {T("tema_koyu"): "dark", T("tema_acik"): "light", T("tema_sistem"): "system"}
        tema_ters = {"dark": T("tema_koyu"), "light": T("tema_acik"), "system": T("tema_sistem")}

        def tema_degistir(secim):
            deger = tema_kod.get(secim, "dark")
            ctk.set_appearance_mode(deger)
            self.ayar["tema"] = deger
            ayar_kaydet(self.ayar)

        tema_menu = ctk.CTkOptionMenu(tema_satir, values=tema_secenek,
                                      width=120, command=tema_degistir)
        tema_menu.set(tema_ters.get(self.ayar.get("tema", "dark"), T("tema_koyu")))
        tema_menu.pack(side="right")

        # Sarki sayisi
        sayi_satir = ctk.CTkFrame(tercih, fg_color="transparent")
        sayi_satir.pack(fill="x", padx=14, pady=(6, 4))
        ctk.CTkLabel(sayi_satir, text=T("sarki_lbl"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        self._sayi_deger_lbl = ctk.CTkLabel(sayi_satir,
                                            text=str(self.ayar.get("sarki_sayisi", 100)),
                                            font=ctk.CTkFont(size=13, weight="bold"),
                                            text_color="#4a9eff")
        self._sayi_deger_lbl.pack(side="right")

        def sayi_degisti(v):
            deger = int(round(v / 10) * 10)
            if deger < 10:
                deger = 10
            self._sayi_deger_lbl.configure(text=str(deger))
            self.ayar["sarki_sayisi"] = deger
            ayar_kaydet(self.ayar)
            try:
                self.sanatci_radio.configure(text=T("mod_sanatci", n=deger))
                self._mod_degisti()
            except Exception:
                pass

        kaydirici = ctk.CTkSlider(tercih, from_=10, to=200, number_of_steps=19,
                                  command=sayi_degisti)
        kaydirici.set(self.ayar.get("sarki_sayisi", 100))
        kaydirici.pack(fill="x", padx=14, pady=(0, 4))
        ctk.CTkLabel(tercih, text=T("sarki_aralik"),
                     font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=14, pady=(0, 8))

        # Ses kalitesi
        kal_satir = ctk.CTkFrame(tercih, fg_color="transparent")
        kal_satir.pack(fill="x", padx=14, pady=(4, 6))
        ctk.CTkLabel(kal_satir, text=T("kalite_lbl"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        def kalite_degisti(secim):
            self.ayar["kalite"] = secim.replace(" kbps", "")
            ayar_kaydet(self.ayar)

        kal_menu = ctk.CTkOptionMenu(kal_satir,
                                     values=["128 kbps", "192 kbps", "320 kbps"],
                                     width=120, command=kalite_degisti)
        kal_menu.set(f"{self.ayar.get('kalite', '320')} kbps")
        kal_menu.pack(side="right")

        # YouTube Top ulkesi
        ulke_satir = ctk.CTkFrame(tercih, fg_color="transparent")
        ulke_satir.pack(fill="x", padx=14, pady=(4, 12))
        ctk.CTkLabel(ulke_satir, text=T("ulke_lbl"),
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        ULKELER = {"Türkiye": "TR", "Global": "Global", "ABD": "US",
                   "Almanya": "DE", "İngiltere": "UK", "Fransa": "FR"}
        ulke_ters = {v: k for k, v in ULKELER.items()}

        def ulke_degisti(secim):
            self.ayar["ulke"] = ULKELER.get(secim, "TR")
            ayar_kaydet(self.ayar)

        ulke_menu = ctk.CTkOptionMenu(ulke_satir, values=list(ULKELER.keys()),
                                      width=120, command=ulke_degisti)
        ulke_menu.set(ulke_ters.get(self.ayar.get("ulke", "TR"), "Türkiye"))
        ulke_menu.pack(side="right")

        # --- Spotify API ---
        if SPOTIFY_VAR:
            sp_kutu = ctk.CTkFrame(pencere)
            sp_kutu.pack(fill="x", padx=20, pady=8)
            ctk.CTkLabel(sp_kutu, text=T("spotify_baslik"),
                         font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=14, pady=(12, 2))
            ctk.CTkLabel(sp_kutu, text=T("spotify_nasil"),
                         font=ctk.CTkFont(size=10), text_color="gray").pack(anchor="w", padx=14, pady=(0, 6))

            sp_id = ctk.CTkEntry(sp_kutu, placeholder_text=T("spotify_id_ph"))
            sp_id.pack(fill="x", padx=14, pady=3)
            sp_id.insert(0, self.ayar.get("spotify_id", ""))

            sp_secret = ctk.CTkEntry(sp_kutu, placeholder_text=T("spotify_secret_ph"), show="•")
            sp_secret.pack(fill="x", padx=14, pady=3)
            sp_secret.insert(0, self.ayar.get("spotify_secret", ""))

            def sp_kaydet(*_):
                self.ayar["spotify_id"] = sp_id.get().strip()
                self.ayar["spotify_secret"] = sp_secret.get().strip()
                ayar_kaydet(self.ayar)
            sp_id.bind("<KeyRelease>", sp_kaydet)
            sp_secret.bind("<KeyRelease>", sp_kaydet)
            ctk.CTkLabel(sp_kutu, text="", height=4).pack()

        # Cikti klasoru
        alt = ctk.CTkFrame(pencere)
        alt.pack(fill="x", padx=20, pady=8)
        yol = os.path.join(uygulama_klasoru(), "music")
        ctk.CTkLabel(alt, text=T("konum_lbl"), font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=14, pady=(12, 0))
        ctk.CTkLabel(alt, text=yol, font=ctk.CTkFont(size=11), text_color="gray", wraplength=390).pack(anchor="w", padx=14, pady=(0, 6))

        def klasoru_ac():
            try:
                os.makedirs(yol, exist_ok=True)
                os.startfile(yol)
            except Exception:
                pass
        ctk.CTkButton(alt, text=T("klasoru_ac"), width=120, command=klasoru_ac).pack(anchor="w", padx=14, pady=(0, 14))

    def _arayuzu_yenile(self):
        # Dil degisince tum widget'lari silip arayuzu yeniden kur
        eski_sira = list(self.sira_listesi)
        for w in self.winfo_children():
            w.destroy()
        self._arayuz_kur()
        self.sira_listesi = eski_sira
        self._sirayi_ciz()
        # guncelleme bildirimi hala gecerliyse tekrar goster
        if self.uzak_surum and _surum_yeni_mi(self.uzak_surum, SURUM):
            self._bildirimi_goster(self.uzak_surum)

    def _bitti(self):
        self.calisiyor = False
        self.baslat_btn.configure(state="normal", text=T("baslat"))
        self.sira_listesi.clear()
        self._sirayi_ciz()


if __name__ == "__main__":
    # Yaninda indirilmis guncel kod varsa onu calistir (kendini gunceller)
    try:
        if getattr(sys, 'frozen', False):
            guncel = os.path.join(veri_klasoru(), "guncel_muzik_indirici.py")
            bu_dosya = os.environ.get("MI_GUNCEL_CALISIYOR")
            if os.path.exists(guncel) and not bu_dosya:
                import runpy
                os.environ["MI_GUNCEL_CALISIYOR"] = "1"
                runpy.run_path(guncel, run_name="__main__")
                sys.exit(0)
    except Exception:
        pass  # guncel kod bozuksa gomulu surumle devam et

    app = Uygulama()
    app.mainloop()
