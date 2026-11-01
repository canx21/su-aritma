# -*- coding: utf-8 -*-
"""A.A. SU ARITMA SİSTEMLERİ - Telefon / Web Arayüz Sunucusu"""
import os, sys, sqlite3, socket
from datetime import date
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

ROOT = os.path.dirname(os.path.abspath(sys.argv[0]))
DB = os.path.join(ROOT, 'su_aritma.db')

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def fmt(s):
    try: return date.fromisoformat(s).strftime('%d.%m.%Y')
    except (ValueError, TypeError): return s or ''

def cur(val):
    try:
        v = float(val)
        return f"{v:,.0f} TL".replace(',', '.')
    except (ValueError, TypeError):
        return "0 TL"

def temizle_telefon_whatsapp(tel):
    if not tel: return ''
    rakamlar = ''.join(filter(str.isdigit, str(tel)))
    if rakamlar.startswith('0'): rakamlar = rakamlar[1:]
    if not rakamlar.startswith('90') and len(rakamlar) == 10: rakamlar = '90' + rakamlar
    return rakamlar

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>A.A. Su Arıtma Mobil</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f1f5f9; margin: 0; padding: 12px; color: #0f172a; }
        h1 { font-size: 18px; color: #0f172a; margin: 0 0 4px 0; }
        .sub { font-size: 12px; color: #64748b; margin-bottom: 12px; }
        .nav { display: flex; gap: 6px; overflow-x: auto; padding-bottom: 8px; margin-bottom: 12px; }
        .nav a { background: #0284c7; color: white; padding: 8px 12px; text-decoration: none; border-radius: 6px; font-size: 12px; font-weight: bold; white-space: nowrap; }
        .nav a.active { background: #0f172a; }
        .card { background: white; padding: 14px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 10px; }
        .card-header { font-weight: bold; font-size: 14px; margin-bottom: 4px; display: flex; justify-content: space-between; }
        .card-body { font-size: 12px; color: #334155; line-height: 1.5; }
        .badge { background: #e2e8f0; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; }
        .btn { background: #16a34a; color: white; padding: 6px 10px; border: none; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold; display: inline-block; }
        .btn-wa { background: #25D366; }
        .btn-map { background: #0284c7; }
        input, select { width: 100%; padding: 10px; box-sizing: border-box; margin-top: 4px; margin-bottom: 12px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 14px; }
        label { font-size: 12px; font-weight: bold; color: #334155; }
        button { background: #0284c7; color: white; border: none; padding: 12px; width: 100%; border-radius: 6px; font-weight: bold; font-size: 14px; cursor: pointer; }
    </style>
</head>
<body>
    <h1>💧 A.A. SU ARITMA SİSTEMLERİ</h1>
    <div class="sub">Mobil Takip Paneli</div>
    
    <div class="nav">
        <a href="/" {% if aktif == 'panel' %}class="active"{% endif %}>Ana Panel</a>
        <a href="/musteriler" {% if aktif == 'musteriler' %}class="active"{% endif %}>Müşteriler</a>
        <a href="/bugun" {% if aktif == 'bugun' %}class="active"{% endif %}>Bugün Servis</a>
        <a href="/borclar" {% if aktif == 'borclar' %}class="active"{% endif %}>Borçlar</a>
        <a href="/bakim" {% if aktif == 'bakim' %}class="active"{% endif %}>Bakım Takip</a>
        <a href="/yeni_musteri" {% if aktif == 'yeni_musteri' %}class="active"{% endif %}>+ Yeni Müşteri</a>
    </div>

    {% if aktif == 'panel' %}
        <div class="card">
            <div class="card-header">📊 Genel Özet</div>
            <div class="card-body">
                <p><b>Toplam Müşteri:</b> {{ m_sayisi }}</p>
                <p><b>Bugün Servis:</b> {{ s_sayisi }}</p>
                <p style="color: #dc2626;"><b>Toplam Alacak:</b> {{ toplam_alacak }}</p>
                <p style="color: #047857;"><b>Kasa Bakiyesi:</b> {{ kasa_bakiye }}</p>
            </div>
        </div>
    {% elif aktif == 'musteriler' %}
        {% for m in musteriler %}
        <div class="card">
            <div class="card-header">
                <span>{{ m.name }}</span>
                <span class="badge">{{ m.district or 'Diyarbakır' }}</span>
            </div>
            <div class="card-body">
                <p>📞 {{ m.phone or 'Telefon Yok' }}</p>
                <p>📍 {{ m.address or 'Adres Yok' }}</p>
                <p>🛠️ Cihaz: {{ m.device or 'KAPALI KASA' }}</p>
                <div style="margin-top: 8px;">
                    {% if m.phone %}
                    <a class="btn btn-wa" href="https://wa.me/{{ m.whatsapp }}?text=Merhaba%20{{ m.name }},%20A.A.%20Su%20Arıtma%20Sistemleri%20olarak%20sağlıklı%20günler%20dileriz." target="_blank">WhatsApp</a>
                    {% endif %}
                    {% if m.address %}
                    <a class="btn btn-map" href="https://www.google.com/maps/search/?api=1&query={{ m.address }},%20{{ m.district }}" target="_blank">Konum</a>
                    {% endif %}
                </div>
            </div>
        </div>
        {% endfor %}
    {% elif aktif == 'bugun' %}
        {% for b in bugun_listesi %}
        <div class="card">
            <div class="card-header">
                <span>{{ b.customer_name }}</span>
                <span style="color:#0284c7;">{{ b.total }} TL</span>
            </div>
            <div class="card-body">
                <p>📞 {{ b.phone }}</p>
                <p>📍 {{ b.address }}</p>
                <p>🔧 İşlem: {{ b.operation }}</p>
            </div>
        </div>
        {% endfor %}
    {% elif aktif == 'borclar' %}
        {% for d in borclar_listesi %}
        <div class="card">
            <div class="card-header">
                <span>{{ d.name }}</span>
                <span style="color:#dc2626; font-weight:bold;">{{ d.kalan }}</span>
            </div>
            <div class="card-body">
                <p>📞 {{ d.phone }}</p>
                <p>📝 {{ d.aciklama }}</p>
            </div>
        </div>
        {% endfor %}
    {% elif aktif == 'bakim' %}
        {% for bk in bakim_listesi %}
        <div class="card">
            <div class="card-header">
                <span>{{ bk.name }}</span>
                <span style="color: {% if bk.gecikti %}#dc2626{% else %}#16a34a{% endif %}; font-weight:bold;">{{ bk.durum }}</span>
            </div>
            <div class="card-body">
                <p>📞 {{ bk.phone }}</p>
                <p>📅 Bakım Tarihi: {{ bk.next_maintenance }}</p>
                <p>📍 İlçe: {{ bk.district }}</p>
            </div>
        </div>
        {% endfor %}
    {% elif aktif == 'yeni_musteri' %}
        <div class="card">
            <form method="POST">
                <label>Müşteri Adı Soyadı *</label>
                <input type="text" name="name" required>
                <label>Telefon</label>
                <input type="text" name="phone">
                <label>İlçe</label>
                <input type="text" name="district" value="KAYAPINAR">
                <label>Adres</label>
                <input type="text" name="address">
                <label>Cihaz Türü</label>
                <input type="text" name="device" value="KAPALI KASA">
                <button type="submit">KAYDET</button>
            </form>
        </div>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def panel():
    with get_db() as conn:
        m_sayisi = conn.execute('SELECT count(*) FROM customers').fetchone()[0]
        s_sayisi = conn.execute('SELECT count(*) FROM bugun_servis').fetchone()[0]
        s_borc = conn.execute('SELECT SUM(total_price - paid_price) FROM sales').fetchone()[0] or 0
        srv_borc = conn.execute('SELECT SUM(total - paid) FROM services').fetchone()[0] or 0
        toplam_alacak = cur(s_borc + srv_borc)
        bakiye = conn.execute("SELECT COALESCE(SUM(CASE WHEN kind='Gelir' THEN amount ELSE -amount END),0) FROM cash").fetchone()[0]
    return render_template_string(HTML_TEMPLATE, aktif='panel', m_sayisi=m_sayisi, s_sayisi=s_sayisi, toplam_alacak=toplam_alacak, kasa_bakiye=cur(bakiye))

@app.route('/musteriler')
def musteriler():
    with get_db() as conn:
        rows = conn.execute('SELECT * FROM customers ORDER BY id DESC').fetchall()
        musteriler = [dict(r, whatsapp=temizle_telefon_whatsapp(r['phone'])) for r in rows]
    return render_template_string(HTML_TEMPLATE, aktif='musteriler', musteriler=musteriler)

@app.route('/bugun')
def bugun():
    with get_db() as conn:
        bugun_listesi = conn.execute('SELECT * FROM bugun_servis ORDER BY id DESC').fetchall()
    return render_template_string(HTML_TEMPLATE, aktif='bugun', bugun_listesi=bugun_listesi)

@app.route('/borclar')
def borclar():
    with get_db() as conn:
        s_debts = conn.execute('SELECT c.name, c.phone, s.device_name as aciklama, (s.total_price - s.paid_price) as kalan FROM sales s JOIN customers c ON c.id=s.customer_id WHERE (s.total_price - s.paid_price) > 0').fetchall()
        srv_debts = conn.execute('SELECT c.name, c.phone, s.operation as aciklama, (s.total - s.paid) as kalan FROM services s JOIN customers c ON c.id=s.customer_id WHERE (s.total - s.paid) > 0').fetchall()
        borclar_listesi = [{'name': d['name'], 'phone': d['phone'], 'aciklama': d['aciklama'] or 'Servis / Satış', 'kalan': cur(d['kalan'])} for d in list(s_debts) + list(srv_debts)]
    return render_template_string(HTML_TEMPLATE, aktif='borclar', borclar_listesi=borclar_listesi)

@app.route('/bakim')
def bakim():
    with get_db() as conn:
        rows = conn.execute('SELECT * FROM customers WHERE next_maintenance IS NOT NULL AND next_maintenance != "" ORDER BY next_maintenance').fetchall()
        bakim_listesi = []
        bugun_tarih = date.today()
        for r in rows:
            try:
                bakim_tarihi = date.fromisoformat(r['next_maintenance'])
                gun_farki = (bakim_tarihi - bugun_tarih).days
                durum = f"Gecikti ({abs(gun_farki)} gün)" if gun_farki < 0 else "Bugün!" if gun_farki == 0 else f"{gun_farki} gün kaldı"
                bakim_listesi.append({'name': r['name'], 'phone': r['phone'], 'district': r['district'], 'next_maintenance': fmt(r['next_maintenance']), 'durum': durum, 'gecikti': gun_farki <= 0})
            except Exception: pass
    return render_template_string(HTML_TEMPLATE, aktif='bakim', bakim_listesi=bakim_listesi)

@app.route('/yeni_musteri', methods=['GET', 'POST'])
def yeni_musteri():
    if request.method == 'POST':
        name = request.form.get('name', '').upper()
        phone = request.form.get('phone', '')
        district = request.form.get('district', '').upper()
        address = request.form.get('address', '').upper()
        device = request.form.get('device', '').upper()
        with get_db() as conn:
            conn.execute('INSERT INTO customers(name, phone, district, address, device, installation, last_service) VALUES(?,?,?,?,?,?,?)',
                         (name, phone, district, address, device, date.today().isoformat(), date.today().isoformat()))
            conn.commit()
        return redirect(url_for('musteriler'))
    return render_template_string(HTML_TEMPLATE, aktif='yeni_musteri')

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=PORT, debug=False)