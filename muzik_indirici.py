import os
import re
import sys
import threading
import queue
import json
import urllib.request

import customtkinter as ctk
import yt_dlp


# ============================================================
#   SURUM & GUNCELLEME AYARLARI
# ============================================================
SURUM = "1.0"

# --- BURAYI KENDI GITHUB BILGILERINLE DOLDUR ---
GH_KULLANICI = "MuammerGrG"           # github kullanici adin
GH_REPO = "music-downloader"          # repo adin
GH_BRANCH = "main"                    # genelde main
# ------------------------------------------------

def _ham_url(dosya):
    return (f"https://raw.githubusercontent.com/"
            f"{GH_KULLANICI}/{GH_REPO}/{GH_BRANCH}/{dosya}")


# ============================================================
#   AYAR KAYDETME (tema, sarki sayisi)
# ============================================================
VARSAYILAN_AYAR = {"tema": "dark", "sarki_sayisi": 100}


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


def guncellemeyi_indir():
    """Guncel muzik_indirici.py'yi cekip exe'nin yanina kaydeder.
    Basari/mesaj doner."""
    try:
        kod_url = _ham_url("muzik_indirici.py")
        with urllib.request.urlopen(kod_url, timeout=15) as r:
            yeni_kod = r.read().decode("utf-8")
        if len(yeni_kod) < 500 or "customtkinter" not in yeni_kod:
            return False, "İndirilen dosya geçersiz görünüyor."
        # exe'nin yanina yaz (bir sonraki acilista bu calisir)
        if getattr(sys, 'frozen', False):
            hedef_dir = os.path.dirname(sys.executable)
        else:
            hedef_dir = os.path.dirname(os.path.abspath(__file__))
        hedef = os.path.join(hedef_dir, "guncel_muzik_indirici.py")
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
    def __init__(self, log_fn, ilerleme_fn):
        self.log = log_fn
        self.ilerleme = ilerleme_fn
        self.ffmpeg = ffmpeg_bul()
        self.iptal = False

    def _ydl_opts(self, hedef_klasor, gorulen, max_indir):
        opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
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
            raise Exception("Kullanici iptal etti")
        if d['status'] == 'finished':
            ad = os.path.basename(d.get('filename', ''))
            self.log(f"   ✓ indirildi: {ad}")

    def sanatci_indir(self, sanatci, adet=100):
        sanatci = sanatci.strip()
        if not sanatci:
            return
        music_kok = os.path.join(uygulama_klasoru(), "music")
        hedef = os.path.join(music_kok, sanatci)
        os.makedirs(hedef, exist_ok=True)
        gorulen = set()
        self.log(f"\n♪ {sanatci.upper()} — en iyi {adet} orijinal sarki")
        arama = f"ytsearch{adet * 2}:{sanatci} sarkilari"
        opts = self._ydl_opts(hedef, gorulen, adet)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([arama])
        except yt_dlp.utils.MaxDownloadsReached:
            self.log(f"   {adet} sarki tamamlandi.")
        except Exception as e:
            self.log(f"   ! hata: {e}")
        klasoru_temizle(hedef, self.log)

    def parca_indir(self, sorgu):
        sorgu = sorgu.strip()
        if not sorgu:
            return
        music_kok = os.path.join(uygulama_klasoru(), "music")
        hedef = os.path.join(music_kok, "Parcalar")
        os.makedirs(hedef, exist_ok=True)
        gorulen = set()
        self.log(f"\n♪ '{sorgu}' araniyor (orijinal, en cok dinlenen)")
        # 5 aday tara, filtreden gecen ILK 1 orijinali indir
        arama = f"ytsearch5:{sorgu}"
        opts = self._ydl_opts(hedef, gorulen, 1)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([arama])
        except yt_dlp.utils.MaxDownloadsReached:
            pass
        except Exception as e:
            self.log(f"   ! hata: {e}")
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
        ctk.CTkLabel(sol, text=f"Orijinal, MP3 320 kbps   ·   v{SURUM}",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w")
        ctk.CTkButton(ust, text="⚙", width=40, height=40,
                      font=ctk.CTkFont(size=18),
                      fg_color="gray25", hover_color="gray35",
                      command=self._ayarlari_ac).pack(side="right", anchor="n")

        # Mod secimi
        self.mod = ctk.StringVar(value="sanatci")
        mod_cerceve = ctk.CTkFrame(self)
        mod_cerceve.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(mod_cerceve, text="Mod:",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(12, 8), pady=10)
        self.sanatci_radio = ctk.CTkRadioButton(
            mod_cerceve, text=f"Sanatçının en iyileri ({self.ayar.get('sarki_sayisi', 100)})",
            variable=self.mod, value="sanatci",
            command=self._mod_degisti)
        self.sanatci_radio.pack(side="left", padx=8, pady=10)
        ctk.CTkRadioButton(mod_cerceve, text="Tek parça (şarkı adı)",
                           variable=self.mod, value="parca",
                           command=self._mod_degisti).pack(side="left", padx=8, pady=10)

        # Giris + ekle
        giris_cerceve = ctk.CTkFrame(self, fg_color="transparent")
        giris_cerceve.pack(fill="x", padx=20, pady=(0, 6))
        self.giris = ctk.CTkEntry(giris_cerceve,
                                  placeholder_text="Örn: Tarkan   veya   Tarkan Kuzu Kuzu",
                                  height=40, font=ctk.CTkFont(size=14))
        self.giris.pack(side="left", fill="x", expand=True)
        self.giris.bind("<Return>", lambda e: self._siraya_ekle())
        ctk.CTkButton(giris_cerceve, text="＋ Sıraya Ekle", width=130, height=40,
                      command=self._siraya_ekle).pack(side="left", padx=(8, 0))

        # Sira (kuyruk)
        sira_ust = ctk.CTkFrame(self, fg_color="transparent")
        sira_ust.pack(fill="x", padx=20, pady=(8, 0))
        ctk.CTkLabel(sira_ust, text="İndirme Sırası",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        ctk.CTkButton(sira_ust, text="Temizle", width=70, height=26,
                      fg_color="gray30", hover_color="gray20",
                      command=self._sirayi_temizle).pack(side="right")

        self.sira_kutu = ctk.CTkTextbox(self, height=90, font=ctk.CTkFont(size=13))
        self.sira_kutu.pack(fill="x", padx=20, pady=(4, 8))
        self.sira_kutu.configure(state="disabled")
        self.sira_listesi = []

        # Baslat butonu
        self.baslat_btn = ctk.CTkButton(self, text="▼  İNDİRMEYİ BAŞLAT",
                                        height=46, font=ctk.CTkFont(size=16, weight="bold"),
                                        command=self._baslat)
        self.baslat_btn.pack(fill="x", padx=20, pady=6)

        # Ilerleme
        self.ilerleme_bar = ctk.CTkProgressBar(self)
        self.ilerleme_bar.pack(fill="x", padx=20, pady=(4, 2))
        self.ilerleme_bar.set(0)

        # Log
        ctk.CTkLabel(self, text="Durum",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(6, 0))
        self.log_kutu = ctk.CTkTextbox(self, font=ctk.CTkFont(size=12), wrap="word")
        self.log_kutu.pack(fill="both", expand=True, padx=20, pady=(2, 16))
        self.log_kutu.configure(state="disabled")

        if not ffmpeg_bul():
            self._log("⚠ ffmpeg.exe bulunamadı — MP3 dönüşümü çalışmayabilir.")

    def _mod_degisti(self):
        if self.mod.get() == "sanatci":
            self.giris.configure(placeholder_text="Örn: Tarkan   (en iyi 100 orijinal iner)")
        else:
            self.giris.configure(placeholder_text="Örn: Tarkan Kuzu Kuzu   (tek şarkı)")

    def _siraya_ekle(self):
        metin = self.giris.get().strip()
        if not metin:
            return
        # Virgulle birden fazla girilebilir
        for parca in metin.split(','):
            parca = parca.strip()
            if parca:
                self.sira_listesi.append((self.mod.get(), parca))
        self.giris.delete(0, "end")
        self._sirayi_ciz()

    def _sirayi_ciz(self):
        self.sira_kutu.configure(state="normal")
        self.sira_kutu.delete("1.0", "end")
        for i, (mod, deger) in enumerate(self.sira_listesi, 1):
            etiket = "🎤 Sanatçı" if mod == "sanatci" else "🎵 Parça"
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
            self._log("Önce sıraya en az bir şey ekle.")
            return
        self.calisiyor = True
        self.baslat_btn.configure(state="disabled", text="İNDİRİLİYOR...")
        gorevler = list(self.sira_listesi)
        threading.Thread(target=self._calis, args=(gorevler,), daemon=True).start()

    def _calis(self, gorevler):
        def log(m): self.mesaj_kuyrugu.put(("log", m))
        def ilerleme(v): self.mesaj_kuyrugu.put(("ilerleme", v))

        ind = Indirici(log, ilerleme)
        toplam = len(gorevler)
        for i, (mod, deger) in enumerate(gorevler):
            ilerleme(i / toplam)
            if mod == "sanatci":
                ind.sanatci_indir(deger, self.ayar.get("sarki_sayisi", 100))
            else:
                ind.parca_indir(deger)
        ilerleme(1.0)
        kayit_yeri = os.path.join(uygulama_klasoru(), "music")
        log(f"\n✅ HEPSİ BİTTİ!\n📁 Konum: {kayit_yeri}")
        self.mesaj_kuyrugu.put(("bitti", None))

    def _guncelleme_kontrol_arka(self):
        uzak, yeni_var = guncelleme_kontrol()
        if yeni_var:
            self.uzak_surum = uzak
            self.mesaj_kuyrugu.put(("guncelleme", uzak))

    def _bildirimi_goster(self, uzak):
        self.bildirim_btn.configure(
            text=f"🔔  Güncelleme mevcut: v{uzak}  —  yüklemek için tıkla")
        self.bildirim_serit.pack(fill="x", side="top", before=self._ust_cerceve)

    def _ayarlari_ac(self):
        pencere = ctk.CTkToplevel(self)
        pencere.title("Ayarlar")
        pencere.geometry("460x580")
        pencere.transient(self)
        try:
            pencere.after(200, lambda: pencere.iconbitmap(kaynak_yolu("logo.ico")))
        except Exception:
            pass

        ctk.CTkLabel(pencere, text="⚙  Ayarlar",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=20, pady=(18, 10))

        # Surum bilgisi
        kutu = ctk.CTkFrame(pencere)
        kutu.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(kutu, text=f"Yüklü sürüm:  v{SURUM}",
                     font=ctk.CTkFont(size=14)).pack(anchor="w", padx=14, pady=(12, 2))

        if self.uzak_surum and _surum_yeni_mi(self.uzak_surum, SURUM):
            durum = ctk.CTkLabel(kutu, text=f"🔔 Yeni sürüm var: v{self.uzak_surum}",
                                 font=ctk.CTkFont(size=14, weight="bold"),
                                 text_color="#4caf50")
            durum.pack(anchor="w", padx=14, pady=2)

            ilerleme_lbl = ctk.CTkLabel(kutu, text="", font=ctk.CTkFont(size=12),
                                        text_color="gray")
            ilerleme_lbl.pack(anchor="w", padx=14, pady=(4, 2))

            def indir():
                indir_btn.configure(state="disabled", text="İndiriliyor...")
                ilerleme_lbl.configure(text="Güncelleme çekiliyor, bekle...")
                def isle():
                    ok, mesaj = guncellemeyi_indir()
                    def bitir():
                        ilerleme_lbl.configure(
                            text=mesaj,
                            text_color="#4caf50" if ok else "#e05555")
                        if ok:
                            indir_btn.configure(text="✓ İndirildi — yeniden başlat")
                        else:
                            indir_btn.configure(state="normal", text="Tekrar dene")
                    self.after(0, bitir)
                threading.Thread(target=isle, daemon=True).start()

            indir_btn = ctk.CTkButton(kutu, text="⬇  İndir ve Kur", command=indir)
            indir_btn.pack(anchor="w", padx=14, pady=(6, 14))
        else:
            ctk.CTkLabel(kutu, text="En güncel sürümü kullanıyorsun ✓",
                         font=ctk.CTkFont(size=13), text_color="gray").pack(anchor="w", padx=14, pady=(2, 12))

            def tekrar_kontrol():
                kontrol_btn.configure(state="disabled", text="Kontrol ediliyor...")
                def isle():
                    uzak, yeni = guncelleme_kontrol()
                    def bitir():
                        kontrol_btn.configure(state="normal", text="Güncellemeleri Denetle")
                        if yeni:
                            self.uzak_surum = uzak
                            pencere.destroy()
                            self._bildirimi_goster(uzak)
                            self._ayarlari_ac()
                    self.after(0, bitir)
                threading.Thread(target=isle, daemon=True).start()

            kontrol_btn = ctk.CTkButton(kutu, text="Güncellemeleri Denetle",
                                        command=tekrar_kontrol)
            kontrol_btn.pack(anchor="w", padx=14, pady=(0, 14))

        # --- Tercihler: tema + sarki sayisi ---
        tercih = ctk.CTkFrame(pencere)
        tercih.pack(fill="x", padx=20, pady=8)

        # Tema
        tema_satir = ctk.CTkFrame(tercih, fg_color="transparent")
        tema_satir.pack(fill="x", padx=14, pady=(12, 6))
        ctk.CTkLabel(tema_satir, text="Tema:",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        def tema_degistir(secim):
            harita = {"Koyu": "dark", "Açık": "light", "Sistem": "system"}
            deger = harita.get(secim, "dark")
            ctk.set_appearance_mode(deger)
            self.ayar["tema"] = deger
            ayar_kaydet(self.ayar)

        ters_harita = {"dark": "Koyu", "light": "Açık", "system": "Sistem"}
        tema_menu = ctk.CTkOptionMenu(tema_satir, values=["Koyu", "Açık", "Sistem"],
                                      width=120, command=tema_degistir)
        tema_menu.set(ters_harita.get(self.ayar.get("tema", "dark"), "Koyu"))
        tema_menu.pack(side="right")

        # Sarki sayisi (sadece sanatci modu)
        sayi_satir = ctk.CTkFrame(tercih, fg_color="transparent")
        sayi_satir.pack(fill="x", padx=14, pady=(6, 4))
        ctk.CTkLabel(sayi_satir, text="Sanatçı başına şarkı:",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")
        self._sayi_deger_lbl = ctk.CTkLabel(sayi_satir,
                                            text=str(self.ayar.get("sarki_sayisi", 100)),
                                            font=ctk.CTkFont(size=13, weight="bold"),
                                            text_color="#4a9eff")
        self._sayi_deger_lbl.pack(side="right")

        def sayi_degisti(v):
            deger = int(round(v / 10) * 10)  # 10'un katlarina yuvarla
            if deger < 10:
                deger = 10
            self._sayi_deger_lbl.configure(text=str(deger))
            self.ayar["sarki_sayisi"] = deger
            ayar_kaydet(self.ayar)
            try:
                self.sanatci_radio.configure(text=f"Sanatçının en iyileri ({deger})")
                self._mod_degisti()
            except Exception:
                pass

        kaydirici = ctk.CTkSlider(tercih, from_=10, to=200, number_of_steps=19,
                                  command=sayi_degisti)
        kaydirici.set(self.ayar.get("sarki_sayisi", 100))
        kaydirici.pack(fill="x", padx=14, pady=(0, 4))
        ctk.CTkLabel(tercih, text="10 – 200 arası",
                     font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=14, pady=(0, 12))

        # Cikti klasoru
        alt = ctk.CTkFrame(pencere)
        alt.pack(fill="x", padx=20, pady=8)
        yol = os.path.join(uygulama_klasoru(), "music")
        ctk.CTkLabel(alt, text="İndirme konumu:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=14, pady=(12, 0))
        ctk.CTkLabel(alt, text=yol, font=ctk.CTkFont(size=11), text_color="gray", wraplength=380).pack(anchor="w", padx=14, pady=(0, 6))

        def klasoru_ac():
            try:
                os.startfile(yol)
            except Exception:
                pass
        ctk.CTkButton(alt, text="📁 Klasörü Aç", width=120, command=klasoru_ac).pack(anchor="w", padx=14, pady=(0, 14))

    def _bitti(self):
        self.calisiyor = False
        self.baslat_btn.configure(state="normal", text="▼  İNDİRMEYİ BAŞLAT")
        self.sira_listesi.clear()
        self._sirayi_ciz()


if __name__ == "__main__":
    # Yaninda indirilmis guncel kod varsa onu calistir (kendini gunceller)
    try:
        if getattr(sys, 'frozen', False):
            yan_dir = os.path.dirname(sys.executable)
            guncel = os.path.join(yan_dir, "guncel_muzik_indirici.py")
            # Sonsuz donguyu onle: bu kodun kendisi zaten guncel dosyaysa atla
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
