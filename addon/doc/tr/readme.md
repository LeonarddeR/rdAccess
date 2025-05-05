# Uzak Masaüstü Erişilebilirliği #

* Yazarlar: [Leonard de Ruijter][1]
* [En son kararlı sürümü indirin][2]
* NVDA uyumluluğu: 2024.1 ve sonrası

Uzak Masaüstü Erişilebilirliği eklentisi (uzak masaüstü erişilebilirliği)
Microsoft uzak masaüstü, Citrix veya VMware Horizon uzak oturumları için
NVDA'ya destek ekler.  NVDA'daki hem istemciye hem de sunucuya
yüklendiğinde, sunucuda oluşturulan konuşma ve Braille, istemci makinesinde
Braille'de konuşulacak ve görüntülenecektir.  Bu, bir uzak sistemi
yönetmenin yerel sistemi çalıştırmak kadar sorunsuz hissettiği bir kullanıcı
deneyimini sağlar.

## Özellikler

* Microsoft uzak masaüstü (Azure Virtual Masaüstü ve Microsoft Cloud PC
  dahil), Citrix ve VMware Horizon için destek
* Konuşma ve braille çıktısı
* NVDA'nın otomatik braille ekran algılamasını kullanarak uzaktan braille'in
  otomatik olarak algılanması
* NVDA'nın ayarlar iletişim kutusunda devre dışı bırakılabilen özel bir
  algılama işlemi kullanarak uzaktan konuşmanın otomatik olarak algılanması
* Bir sunucuda çalışan NVDA'nın taşınabilir kopyaları için destek (Citrix
  için ek yapılandırma gerekli)
* Bir istemcide çalışan taşınabilir NVDA kopyaları için tam destek
  (eklentiyi yüklemek için ek yönetici ayrıcalığı gerekmez)
* Aynı anda birden fazla aktif istemci oturumu
* Uzak masaüstü, NVDA başladıktan sonra anında kullanılabilir
* Uzak oturumdan ayrılmadan belirli sentezleyici ve braille ekran ayarlarını
  kontrol etme yeteneği
* Güvenli masaüstlerine erişirken kullanıcı oturumundan konuşma ve braille
  kullanabilme özelliği

## Değişiklik günlüğü

### Sürüm 1.5

* Uzak Masaüstü Erişilebilirliği Ayar panelinde
  [#23](https://github.com/leonardder/rdaccess/pull/23) bir düğme
  aracılığıyla bir hata ayıklama teşhis raporu oluşturma olanağı eklendi.
* NVDA 2025.1 ve daha yeni sürümlerde çok satırlı braille ekranları için
  destek [#19](https://github.com/leonardder/rdAccess/pull/13).
* En düşük uyumlu NVDA sürümü artık 2024.1'dir. Önceki sürümler için destek
  kaldırıldı.
* İstemci bağlantısı bildirimleri eklendi
  [#25](https://github.com/leonardder/rdAccess/pull/25).
* Güncellenmiş RDPipe bağımlılığı.
* Güncellenmiş çeviriler.

### Sürüm 1.4

* Yeni kararlı sürüm.

### Sürüm 1.3

* Bozuk braille görüntüleme hareketleri düzeltildi.

### Sürüm 1.2

* [Ruff kullanın](https://github.com/astral-sh/ruff) as a formatter and
  linter. [#13](https://github.com/leonardder/rdAccess/pull/13).
* Sunucudaki konuşmayı duraklatırken istemcideki NVDA'nın bir hata
  oluşturduğu bir sorun düzeltildi.
* `winAPI.secureDesktop.post_secureDesktopStateChange` desteği düzeltildi.
* Sunucuda geliştirilmiş sürücü başlatma.

### Sürüm 1.1

* Braille ekranlarının otomatik olarak algılanması için NVDA 2023.3 stili
  cihaz kaydı desteği
  eklendi. [#11](https://github.com/leonardder/rdAccess/pull/11).
* NVDA 2024.1 alfa `winAPI.secureDesktop.post_secureDesktopStateChange`
  uzatma noktası için destek
  eklendi. [#12](https://github.com/leonardder/rdAccess/pull/12).

### Sürüm 1.0

İlk kararlı sürüm.

## Başlarken

1. Uzak Masaüstü Erişilebilirliği eklentisini NVDA'nın hem istemci hem de
   sunucu kopyasına kurun.
1. Uzak sistem, yerel konuşma sentezleyicisini kullanarak otomatik olarak
   konuşmaya başlamalıdır. Değilse, sunucudaki NVDA örneğinde, NVDA'nın
   sentezleyici seçim iletişim kutusundan uzak konuşma sentezleyicisini
   seçin.
1. Braille'i kullanmak için braille ekran seçimi iletişim kutusunu
   kullanarak otomatik braille ekran algılamayı etkinleştirin.

## Yapılandırma

Kurulumdan sonra, Uzak Masaüstü Erişilebilirliği eklentisi, NVDA Menüsünden Tercihler > Ayarlar seçilerek erişilebilen NVDA'nın ayarlar iletişim kutusu kullanılarak yapılandırılabilir...
Ardından, uzak masaüstü kategorisini seçin.

Bu iletişim kutusu aşağıdaki ayarları içerir:

### Şunlar için uzak masaüstü erişilebilirliğini etkinleştir

Bu onay kutuları listesi, eklentinin çalışma modunu kontrol
eder. Aşağıdakiler arasında seçim yapabilirsiniz:

* Gelen bağlantılar (Uzak Masaüstü Sunucusu): Geçerli NVDA örneği bir uzak
  masaüstü sunucusunda çalışıyorsa bu seçeneği seçin.
* Giden bağlantılar (Uzak Masaüstü İstemcisi): Geçerli NVDA örneği, bir veya
  daha fazla sunucuya bağlanan bir uzak masaüstü istemcisinde çalışıyorsa bu
  seçeneği seçin.
* Güvenli Masaüstü geçişi: Güvenli masaüstüne erişirken NVDA'nın kullanıcı
  örneğinden Braille ve konuşma kullanmak istiyorsanız bu seçeneği
  belirleyin. Bunun çalışması için RDAccess eklentisini NVDA'nın güvenli
  masaüstü kopyasında kullanılabilir hale getirmeniz gerektiğini
  unutmayın. Bunun için NVDA'nın ayarlar Genel içerisinde "Oturum açma
  sırasında ve güvenli ekranlarda şu anda kayıtlı ayarları kullan (yönetici
  ayrıcalıkları gerektirir)" seçeneğini belirleyin.

Eklenti ile sorunsuz bir başlangıç ​​sağlamak için tüm seçenekler varsayılan
olarak etkinleştirilir. Ancak, uygun şekilde sunucu veya istemci modunu
devre dışı bırakmaya teşvik edilirsiniz.

### Bağlantı kesintisinden sonra uzak konuşmayı otomatik olarak kurtar

Bu seçenek yalnızca sunucu modunda mevcuttur. Uzaktan konuşma sentezleyicisi
etkin olduğunda ve Braille ekran otomatik tespitine benzer şekilde bağlantı
kaybolduğunda bağlantının otomatik olarak yeniden kurulmasını sağlar.

Bu seçenek varsayılan olarak etkindir. Uzak Masaüstü sunucusunda ses çıkışı
yoksa, bu seçeneği etkin bırakmanız kesinlikle önerilir.

### Uzak Sistemin Sürücü Ayarlarını Kontrol Etmesine İzin Ver

İstemcide etkinleştirildiğinde, bu seçenek sürücü ayarlarını (sentezleyici
sesi ve perdesi gibi) uzak sistemden kontrol etmenizi sağlar. Uzak sistemde
yapılan değişiklikler otomatik şekilde yerel olarak yansıtılacaktır.

### NVDA kapatıldığında istemci desteğini sürdür

NVDA'nın yüklü kopyalarında bulunan bu istemci seçeneği, NVDA çalışmadığında
bile NVDA'nın istemci kısmının uzak masaüstü istemcinize yüklenmesini
sağlar.

Uzak Masaüstü Erişilebilirliği'nin istemci bölümünü kullanmak için Windows
Kayıt Defteri'nde değişiklik yapılması gerekir.  Eklenti, bu değişikliklerin
geçerli kullanıcının profili altında yapılmasını sağlar ve hiçbir idari
ayrıcalık gerektirmez.  Bu nedenle, NVDA yüklendiğinde gerekli
değişiklikleri otomatik olarak uygulayabilir, NVDA'dan çıkarken bu
değişiklikleri geri alabilir ve NVDA'nın taşınabilir sürümleriyle uyumluluk
sağlar.

Bu seçenek varsayılan olarak devre dışı bırakılır. Ancak, yüklü bir kopya
çalıştırıyorsanız ve sistemin tek kullanıcısıysanız, NVDA başladıktan sonra
uzak bir sisteme bağlanırken bu seçeneği düzgün çalışma için
etkinleştirmeniz önerilir.

### Microsoft Uzak Masaüstü desteğini etkinleştir

Bu seçenek varsayılan olarak etkindir ve NVDA başlatılırken Uzak Masaüstü
Erişilebilirliği'nin istemci kısmının Microsoft Uzak Masaüstü istemcisine
(mstsc) yüklenmesini sağlar. Önceki seçenek etkinleştirilerek kalıcı istemci
desteği etkinleştirilmedikçe, NVDA'dan çıkıldığında bu değişiklikler
otomatik olarak geri alınır.

### Citrix çalışma alanı desteğini etkinleştir

Bu seçenek varsayılan olarak etkindir ve NVDA başlatılırken Uzak Masaüstü
Erişilebilirliği'nin istemci kısmının Citrix çalışma alanı uygulamasına
yüklenmesini sağlar. Önceki seçenek etkinleştirilerek kalıcı istemci desteği
etkinleştirilmedikçe, NVDA'dan çıkıldığında bu değişiklikler otomatik olarak
geri alınır.

Bu seçenek yalnızca aşağıdaki durumlarda kullanılabilir:

* Citrix çalışma alanı kurulmuşsa. Uygulamanın kendisindeki sınırlamalar
  nedeniyle uygulamanın Windows Mağazası sürümünün desteklenmediğini
  unutmayın.
* Geçerli kullanıcı bağlamı altında Uzak Masaüstü Erişilebilirliği'ni
  kaydetmek mümkündür. Uygulamayı yükledikten sonra, bunu mümkün kılmak için
  bir kez uzaktan oturum başlatmanız gerekir.

### Bağlantı değişikliklerini şununla bildir

Bu birleşik kutu, uzak bir sistem uzak konuşmayı veya Braille bağlantısını
açtığında ya da kapattığında alınan bildirimleri kontrol etmenizi sağlar.
Aralarında seçim yapabilirsiniz:

* Kapalı (bildirim yok)
* Mesajlar (örn. "Uzak Braille bağlı")
* Sesler (NVDA 2025.1+)
* Hem mesajlar hem de sesler

Seslerin 2025.1'den daha eski NVDA sürümlerinde mevcut olmadığını
unutmayın. Bip sesleri eski sürümlerde kullanılacaktır.

### Tanılama raporunu aç

Bu düğme, JSON çıkışına sahip, hata ayıklamaya yardımcı olabilecek birkaç
teşhis içeren göz atılabilir bir mesaj açar.  [GitHub'da bir sorun
sunarken][4], bu raporu vermeniz istenebilir.

## Citrix'e özgü talimatlar

Uzak Masaüstü Erişilebilirliği'ni Citrix çalışma alanı uygulamasıyla
kullanırken dikkat edilmesi gereken bazı önemli noktalar vardır:

### İstemci tarafı gereksinimleri

1. Uygulamanın Windows Mağazası varyantı *desteklenmez*.
1. Citrix çalışma alanı'nı kurduktan sonra, Uzak Masaüstü
   Erişilebilirliği'nin kendisini kaydetmesine izin vermek için bir kez uzak
   oturum başlatmanız gerekir. Bunun nedeni, uygulamanın ilk defa oturum
   oluşturduğunda sistem yapılandırmasını kullanıcı yapılandırmasına
   kopyalamasıdır. Bundan sonra, Uzak Masaüstü Erişilebilirliği kendisini
   geçerli kullanıcı bağlamı altında kaydedebilir.

### Sunucu tarafı gereksinimi

Citrix Sanal Uygulamalar ve Masaüstleri 2109'da Citrix, sanal kanal izin
verilenler listesini etkinleştirdi. Bu, Uzak Masaüstü gerektirdiği kanal da
dahil olmak üzere üçüncü taraf sanal kanallarına varsayılan olarak izin
verilmediği anlamına gelir. Daha fazla bilgi için [bu Citrix blog
gönderisine
bakın](https://www.citrix.com/blogs/2021/10/14/virtual-channel-allow-list-now-enabled-by-default/)

Uzak Masaüstü Erişilebilirliği tarafından gerekli görülen RdPipe kanalına
açıkça izin verilmesi henüz test edilmemiştir. Şimdilik, izin verilenler
listesini tamamen devre dışı bırakmak muhtemelen en iyi
seçeneğinizdir. Sistem yöneticiniz bundan memnun değilse, [özel konuya bir
bildirim bırakın][3] çekinmeyin.

## Sorunlar ve katkıda bulunma

Bir sorunu bildirmek veya katkıda bulunmak istiyorsanız [Github'daki
sorunlar sayfasına][4] göz atın.

## Dış bileşenler

Bu eklenti, uzak masaüstü istemci desteğini destekleyen trust ile yazılmış
bir kütüphane olan [Rd Pipe](5) sürümüne dayanmaktadır.  RD Pipe, bu
eklentinin bir parçası olarak [GNU Affero Genel Lisansı](6) şartları altında
yeniden dağıtılmaktadır.

[[!tag stable dev beta]]

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess

[3]: https://github.com/leonardder/rdAccess/issues/1

[4]: https://github.com/leonardder/rdAccess/issues

[5]: https://github.com/leonardder/rd_pipe-rs

[6]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
