import flet as ft
import sqlite3
import os
import certifi

# SSL Sertifika Ayarı (Mobilde internet erişimi ve güvenli bağlantılar için)
os.environ["SSL_CERT_FILE"] = certifi.where()

class ServisTakipApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Mobil Servis Takip v10.1"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 10
        # Mobilde ekranın kaydırılabilir olması (klavye açıldığında bozulmaması için)
        self.page.scroll = ft.ScrollMode.ADAPTIVE 
        
        self.db_setup()
        self.init_controls()
        self.init_ui()

    def db_setup(self):
        """Veritabanını mobil uyumlu dizinde oluşturur."""
        try:
            if self.page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]:
                data_path = self.page.data_directory if self.page.data_directory else "."
                db_path = os.path.join(data_path, "servis.db")
            else:
                db_path = "servis.db"

            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS islemler (
                id INTEGER PRIMARY KEY AUTOINCREMENT, is_no TEXT UNIQUE, plaka TEXT, 
                tel TEXT, isim TEXT, sikayet TEXT, cozum TEXT, fiyat TEXT, parca TEXT, teslim TEXT)''')
            self.conn.commit()
        except Exception as e:
            print(f"DB Error: {e}")

    def init_controls(self):
        """Tüm giriş bileşenlerini hazırlar."""
        # HATALI OLAN 'autocapitalization' PARAMETRESİ 'capitalization' OLARAK DÜZELTİLDİ
        self.is_no = ft.TextField(label="İşemri No", border_color=ft.Colors.BLUE, keyboard_type=ft.KeyboardType.NUMBER)
        self.plaka = ft.TextField(label="Plaka", capitalization=ft.TextCapitalization.CHARACTERS)
        self.tel = ft.TextField(label="Telefon", keyboard_type=ft.KeyboardType.PHONE)
        self.isim = ft.TextField(label="İsim", capitalization=ft.TextCapitalization.WORDS)
        self.sikayet = ft.TextField(label="Şikayet Notu", multiline=True, min_lines=2)
        self.cozum = ft.TextField(label="Yapılan İşlem", multiline=True, min_lines=2)
        
        self.fiyat_v = ft.Dropdown(label="Fiyat Durumu", value="FİYAT ONAYI ALINACAK", options=[
            ft.dropdown.Option("FİYAT ONAYI ALINACAK"), ft.dropdown.Option("FİYAT ONAYI ALINDI")])
        
        self.parca_v = ft.Dropdown(label="Parça Durumu", value="SİPARİŞ VERİLECEK", options=[
            ft.dropdown.Option("SİPARİŞ VERİLECEK"), ft.dropdown.Option("SİPARİŞ VERİLDİ BEKLİYOR"), ft.dropdown.Option("PARÇA GELDİ")])
        
        self.teslim_v = ft.Dropdown(label="Teslim Durumu", value="TESLİM EDİLECEK", options=[
            ft.dropdown.Option("TESLİM EDİLECEK"), ft.dropdown.Option("TESLİM EDİLDİ")])

        self.search_bar = ft.TextField(label="🔍 Ara (Plaka, İsim...)", on_change=self.listele)
        self.liste_alani = ft.Column(scroll=ft.ScrollMode.ALWAYS, expand=True)

    def init_ui(self):
        """Alt navigasyon ve ana container yapısını kurar."""
        self.nav_bar = ft.NavigationBar(
            selected_index=0,
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.ADD_CIRCLE_OUTLINE, label="Yeni Kayıt"),
                ft.NavigationBarDestination(icon=ft.Icons.LIST_ALT, label="İşlem Listesi"),
            ],
            on_change=lambda e: self.ekran_guncelle(e.control.selected_index)
        )
        
        self.main_container = ft.Container(content=self.kayit_view(), expand=True)
        self.page.navigation_bar = self.nav_bar
        self.page.add(self.main_container)

    def ekran_guncelle(self, index):
        if index == 0:
            self.main_container.content = self.kayit_view()
        else:
            self.main_container.content = self.liste_view()
            self.listele()
        self.page.update()

    def kayit_view(self):
        return ft.Column([
            ft.Text("🛠️ YENİ KAYIT", size=24, weight="bold"),
            self.is_no, self.plaka, self.tel, self.isim,
            self.sikayet, self.cozum,
            self.fiyat_v, self.parca_v, self.teslim_v,
            ft.FilledButton("KAYDI SİSTEME EKLE", 
                           style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700),
                           height=50, width=500,
                           on_click=self.kaydet)
        ], scroll=ft.ScrollMode.AUTO, expand=True)

    def liste_view(self):
        return ft.Column([
            ft.Text("📋 AKTİF İŞLEMLER", size=24, weight="bold"),
            self.search_bar,
            self.liste_alani
        ], expand=True)

    def kaydet(self, e):
        if not self.is_no.value or not self.plaka.value:
            self.show_snack("Hata: No ve Plaka eksik!", ft.Colors.RED)
            return

        try:
            self.cursor.execute("""INSERT INTO islemler 
                (is_no, plaka, tel, isim, sikayet, cozum, fiyat, parca, teslim) 
                VALUES (?,?,?,?,?,?,?,?,?)""", 
                (self.is_no.value, self.plaka.value, self.tel.value, self.isim.value, 
                 self.sikayet.value, self.cozum.value, 
                 self.fiyat_v.value, self.parca_v.value, self.teslim_v.value))
            self.conn.commit()
            self.temizle()
            
            # Kayıttan sonra listeye geç
            self.nav_bar.selected_index = 1
            self.ekran_guncelle(1)
            self.show_snack("Kayıt başarıyla eklendi!", ft.Colors.GREEN)
        except sqlite3.IntegrityError:
            self.show_snack("Hata: Bu No zaten kayıtlı!", ft.Colors.RED)
        except Exception as ex:
            self.show_snack(f"Hata: {ex}", ft.Colors.RED)

    def listele(self, e=None):
        self.liste_alani.controls.clear()
        search = self.search_bar.value.lower() if self.search_bar.value else ""
        
        if search:
            self.cursor.execute("SELECT * FROM islemler WHERE plaka LIKE ? OR is_no LIKE ? OR isim LIKE ?", 
                                (f'%{search}%', f'%{search}%', f'%{search}%'))
        else:
            self.cursor.execute("SELECT * FROM islemler ORDER BY id DESC")
        
        for row in self.cursor.fetchall():
            is_delivered = row[9] == "TESLİM EDİLDİ"
            card = ft.Card(
                content=ft.Container(
                    padding=10,
                    content=ft.Column([
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.DIRECTIONS_CAR),
                            title=ft.Text(f"{row[2].upper()} ({row[1]})"),
                            subtitle=ft.Text(f"{row[4]} - {row[3]}"),
                        ),
                        ft.Row([
                            ft.Text(f" {row[9]}", color=ft.Colors.GREEN if is_delivered else ft.Colors.ORANGE, size=12, weight="bold"),
                            ft.Row([
                                ft.IconButton(ft.Icons.EDIT, on_click=lambda x, r=row: self.detay_ac(r)),
                                ft.IconButton(ft.Icons.DELETE, icon_color="red", on_click=lambda x, r=row[1]: self.sil(r))
                            ])
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    ])
                )
            )
            self.liste_alani.controls.append(card)
        self.page.update()

    def sil(self, is_no):
        self.cursor.execute("DELETE FROM islemler WHERE is_no = ?", (is_no,))
        self.conn.commit()
        self.listele()

    def show_snack(self, message, color):
        sb = ft.SnackBar(ft.Text(message), bgcolor=color)
        self.page.overlay.append(sb)
        sb.open = True
        self.page.update()

    def temizle(self):
        for field in [self.is_no, self.plaka, self.tel, self.isim, self.sikayet, self.cozum]:
            field.value = ""
        self.page.update()

    def detay_ac(self, row):
        d_sikayet = ft.TextField(label="Şikayet", value=row[5], multiline=True)
        d_cozum = ft.TextField(label="İşlem", value=row[6], multiline=True)
        d_fiyat = ft.Dropdown(value=row[7], options=[ft.dropdown.Option("FİYAT ONAYI ALINACAK"), ft.dropdown.Option("FİYAT ONAYI ALINDI")])
        d_parca = ft.Dropdown(value=row[8], options=[ft.dropdown.Option("SİPARİŞ VERİLECEK"), ft.dropdown.Option("SİPARİŞ VERİLDİ BEKLİYOR"), ft.dropdown.Option("PARÇA GELDİ")])
        d_teslim = ft.Dropdown(value=row[9], options=[ft.dropdown.Option("TESLİM EDİLECEK"), ft.dropdown.Option("TESLİM EDİLDİ")])

        def guncelle(e):
            self.cursor.execute("""UPDATE islemler SET 
                sikayet=?, cozum=?, fiyat=?, parca=?, teslim=? WHERE is_no=?""",
                (d_sikayet.value, d_cozum.value, d_fiyat.value, d_parca.value, d_teslim.value, row[1]))
            self.conn.commit()
            bs.open = False
            self.listele()
            self.page.update()

        bs = ft.BottomSheet(
            content=ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text(f"Düzenle: {row[2]}", size=20, weight="bold"),
                    d_sikayet, d_cozum, d_fiyat, d_parca, d_teslim,
                    ft.FilledButton("GÜNCELLEMEYİ KAYDET", on_click=guncelle, width=500)
                ], scroll=ft.ScrollMode.AUTO, tight=True)
            )
        )
        self.page.overlay.append(bs)
        bs.open = True
        self.page.update()

def main(page: ft.Page):
    ServisTakipApp(page)

if __name__ == "__main__":
    ft.app(target=main)