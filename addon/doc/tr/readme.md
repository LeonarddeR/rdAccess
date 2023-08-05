# Uzak Masaüstü Erişilebilirliği #

* Yazarlar: [Leonard de Ruijter][1]
* [En son beta sürümünü indirin][2]
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

## Yapılandırma

Kurulumdan sonra Uzak masaüstü erişilebilirliği eklentisi, NVDA Menüsünden Tercihler > Ayarlar... seçilerek erişilebilen NVDA'nın ayarlar iletişim kutusu kullanılarak yapılandırılabilir.
Daha sonra, Uzak Masaüstü kategorisini seçin.

Bu iletişim kutusu aşağıdaki ayarları içerir:

### Şunlar için uzak masaüstü erişilebilirliğini etkinleştirin

Bu onay kutusu düğmeleri listesi, eklentinin çalışma modunu kontrol
eder. Aşağıdakiler arasından seçim yapabilirsiniz:

* Gelen bağlantılar (Uzak Masaüstü Sunucusu): Geçerli NVDA örneği bir uzak
  masaüstü sunucusunda çalışıyorsa bu seçeneği seçin

* Giden bağlantılar (Uzak Masaüstü İstemcisi): Geçerli NVDA örneği, bir veya
  daha fazla sunucuya bağlanan bir uzak masaüstü istemcisinde çalışıyorsa bu
  seçeneği seçin

* Güvenli Masaüstü geçişi: : Uzak masaüstüne erişirken NVDA kullanıcı
  örneğinden braille ve konuşma kullanmak istiyorsanız bu seçeneği
  seçin. Bunun çalışması için, NVDA'nın güvenli masaüstü kopyasında Uzak
  Masaüstü Erişilebilirliği eklentisini kullanıma sunmanız gerektiğini
  unutmayın. Bunun için, NVDA'nın genel ayarlarında "Oturum açma sırasında
  ve güvenli ekranlarda (yönetici ayrıcalıkları gerektirir) mevcut kayıtlı
  ayarları kullan" seçeneğini seçin.

Eklentiyle sorunsuz bir başlangıç ​​sağlamak için tüm seçenekler varsayılan
olarak etkindir. Bununla birlikte, sunucu veya istemci modunu uygun şekilde
devre dışı bırakmanız önerilir.

### Bağlantı kesintisinden sonra uzak konuşmayı otomatik olarak kurtar

Bu seçenek yalnızca sunucu modunda kullanılabilir. Uzak Konuşma sentezleyici
etkinken ve bağlantı kesildiğinde bağlantının otomatik olarak yeniden
kurulmasını sağlar. Davranış, braille ekranı otomatik algılama davranışına
çok benzer. Bu aynı zamanda neden sadece konuşma için böyle bir seçeneğin
olduğunu da açıklığa kavuşturuyor. Uzak Braille ekranının yeniden
bağlanması, Braille Ekranı Seçimi iletişim kutusundan Otomatik seçeneği
seçildiğinde otomatik olarak gerçekleştirilir.

Bu seçenek varsayılan olarak etkindir. Uzak Masaüstü sunucusunda ses çıkışı
yoksa, bu seçeneği etkin bırakmanız kesinlikle önerilir.

### Uzak sistemin sürücü ayarlarını kontrol etmesine izin ver

Bu istemci seçeneği etkinleştirildiğinde, uzak sistemden sürücü ayarlarını
(sentezleyici sesi ve perdesi gibi) kontrol etmenizi sağlar. Uzak sistemde
yapılan değişiklikler yerel olarak otomatik olarak yansıtılacaktır. Uzak bir
sistemi kontrol ederken yerel NVDA menüsüne erişimde sorun yaşıyorsanız, bu
seçeneği etkinleştirebilirsiniz. Aksi takdirde, bazı performans düşüşleri
anlamına geleceği için devre dışı bırakmanız önerilir.

### NVDA kapatıldığında istemci desteğini sürdür

Bu istemci seçeneği yalnızca yüklü NVDA kopyalarında
mevcuttur. Etkinleştirildiğinde, NVDA çalışmıyorken bile NVDA'nın istemci
kısmının uzak masaüstü istemcinize yüklenmesini sağlar.

Uzak Masaüstü Erişilebilirliği'nin istemci bölümünü kullanmak için, Windows
Kayıt Defterinde çeşitli değişikliklerin yapılması gerekir. Eklenti, bu
değişikliklerin geçerli kullanıcının profili altında yapılmasını sağlar. Bu
değişiklikler yönetici ayrıcalıkları gerektirmez. Bu nedenle NVDA,
yüklendiğinde gerekli değişiklikleri otomatik olarak uygulayabilir ve
NVDA'dan çıkarken bu değişiklikleri geri alabilir. Bu, eklentinin NVDA'nın
taşınabilir sürümleriyle tamamen uyumlu olmasını sağlar. Bu senaryoya izin
vermek için bu seçenek varsayılan olarak devre dışıdır. Ancak, kurulu bir
kopya çalıştırıyorsanız ve sistemin tek kullanıcısı sizseniz, uzak bir
sisteme bağlanırken NVDA'nın başlatılması veya etkin olmaması durumunda
sorunsuz çalışmayı sağlamak için bu seçeneği etkinleştirmeniz önerilir.

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
  unutmayın
* Geçerli kullanıcı bağlamı altında Uzak Masaüstü Erişilebilirliği'ni
  kaydetmek mümkündür. Uygulamayı yükledikten sonra, bunu mümkün kılmak için
  bir kez uzaktan oturum başlatmanız gerekir

## Citrix'e özel talimatlar

Uzak Masaüstü Erişilebilirliği'ni Citrix çalışma alanı uygulamasıyla
kullanırken dikkat edilmesi gereken bazı önemli noktalar vardır.

### İstemci tarafı gereksinimleri

1. Uygulamanın Windows Mağazası varyantı *desteklenmez*.

2. Citrix çalışma alanı'nı kurduktan sonra, Uzak Masaüstü
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

RDAccess tarafından gerekli görülen RdPipe kanalına açıkça izin verilmesi
henüz test edilmemiştir. Şimdilik, izin verilenler listesini tamamen devre
dışı bırakmak muhtemelen en iyi seçeneğinizdir. Sistem yöneticiniz bundan
memnun değilse, [özel konuya bir satır bırakın][3] çekinmeyin

## Sorunlar ve katkıda bulunma

Bir sorunu bildirmek veya katkıda bulunmak istiyorsanız [Github'daki
sorunlar sayfasına][3] göz atın

## Dış bileşenler

Bu eklenti, uzak masaüstü istemci desteğini destekleyen Rust'ta yazılmış bir
kitaplık olan [RD Pipe][4]'e dayanır. RD Pipe, Free Software Foundation
tarafından yayınlanan [GNU Affero Genel Kamu Lisansının 3. sürümü] [5]
koşulları altında bu eklentinin bir parçası olarak yeniden dağıtılır. Özgür
Yazılım Vakfı tarafından yayınlandı.

[[!tag dev beta]]

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess-beta

[3]: https://github.com/leonardder/rdAccess/issues

[4]: https://github.com/leonardder/rd_pipe-rs

[5]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
