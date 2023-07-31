# Uzak Masaüstü Erişilebilirliği #

* Yazarlar: [Leonard de Ruijter][1]
* [Beta sürümünü indir][2]
* NVDA uyumluluğu: 2023.2 ve sonrası

RDAccess eklentisi (Uzak Masaüstü Erişilebilirliği), Microsoft Uzak
Masaüstü, Citrix veya VMware Horizon kullanarak NVDA'ya uzak masaüstü
oturumlarına erişim desteği ekler. NVDA'ya hem istemciye hem de sunucuya
yüklendiğinde, sunucuda oluşturulan konuşma ve Braille alfabesi istemci
makine tarafından seslendirilir ve böbürlenir. Bu, uzak bir sistemi
yönetmenin yerel sistemi çalıştırmak kadar performanslı olduğu bir kullanıcı
deneyimi sağlar.

## Özellikler

* Microsoft Uzak Masaüstü, Citrix ve VMware Horizon desteği
* Konuşma ve braille çıktısı
* NVDA'nın otomatik braille ekran algılamasını kullanarak uzaktan braille'in
  otomatik olarak algılanması
* NVDA'nın ayarlar iletişim kutusunda devre dışı bırakılabilen özel bir
  algılama işlemi kullanarak uzaktan konuşmanın otomatik olarak algılanması
* Bir sunucuda çalışan taşınabilir NVDA kopyaları için destek (Fitrix için
  ek yapılandırma gereklidir)
* Bir istemcide çalışan taşınabilir NVDA kopyaları için tam destek
  (eklentiyi yüklemek için ek yönetici ayrıcalığı gerekmez)
* Aynı anda birden fazla aktif istemci oturumu
* Uzak masaüstü, NVDA başladıktan sonra anında kullanılabilir
* Uzak oturumdan ayrılmadan belirli sentezleyici ve braille ekran ayarlarını
  kontrol etme yeteneği
* Güvenli masaüstlerine erişirken kullanıcı oturumundan konuşma ve braille
  kullanabilme özelliği

## Başlarken

1. RDAccess'i NVDA'nın hem istemci hem de sunucu kopyasına kurun.
1. Uzak sistem, yerel konuşma sentezleyicisini kullanarak otomatik olarak
   konuşmaya başlamalıdır. Değilse, sunucudaki NVDA örneğinde, NVDA'nın
   sentezleyici seçim iletişim kutusundan uzak konuşma sentezleyicisini
   seçin.
1. Braille'i kullanmak için braille ekran seçimi iletişim kutusunu
   kullanarak otomatik braille ekran algılamayı etkinleştirin.

## Sorunlar ve katkıda bulunma

Bir sorunu bildirmek veya katkıda bulunmak istiyorsanız [Github'daki
sorunlar sayfasına][3] göz atın

## Dış bileşenler

Bu eklenti, uzak masaüstü istemci desteğini destekleyen Rust'ta yazılmış bir
kitaplık olan [RD Pipe][4]'e dayanır. RD Pipe, Free Software Foundation
tarafından yayınlanan [GNU Affero Genel Kamu Lisansının 3. sürümü] [5]
koşulları altında bu eklentinin bir parçası olarak yeniden dağıtılır.

[[!tag dev]]

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess-beta

[3]: https://github.com/leonardder/rdAccess/issues

[4]: https://github.com/leonardder/rd_pipe-rs

[5]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
