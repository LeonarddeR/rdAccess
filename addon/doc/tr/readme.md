# Uzak Masaüstü Erişilebilirliği #

* Yazarlar: [Leonard de Ruijter][1]
* [En son kararlı sürümü indirin][2]
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

## Değişiklik günlüğü

### Sürüm 1.0

İlk kararlı sürüm.

## Başlarken

1. RDAccess'i NVDA'nın hem istemci hem de sunucu kopyasına kurun.
1. Uzak sistem, yerel konuşma sentezleyicisini kullanarak otomatik olarak
   konuşmaya başlamalıdır. Değilse, sunucudaki NVDA örneğinde, NVDA'nın
   sentezleyici seçim iletişim kutusundan uzak konuşma sentezleyicisini
   seçin.
1. Braille'i kullanmak için braille ekran seçimi iletişim kutusunu
   kullanarak otomatik braille ekran algılamayı etkinleştirin.

## Yapılandırma

Kurulumdan sonra, RDAccess eklentisi, NVDA Menüsünden Tercihler > Ayarlar... seçeneğini seçerek erişilebilen NVDA'nın ayarlar iletişim kutusu kullanılarak yapılandırılabilir.
Bundan sonra Uzak Masaüstü kategorisini seçin.

Bu iletişim kutusu aşağıdaki ayarları içerir:

### Şunlar için uzak masaüstü erişilebilirliğini etkinleştirin

Bu onay kutuları listesi, eklentinin çalışma modunu kontrol
eder. Aşağıdakiler arasında seçim yapabilirsiniz:

* Gelen bağlantılar (Uzak Masaüstü Sunucusu): Geçerli NVDA örneği bir uzak
  masaüstü sunucusunda çalışıyorsa bu seçeneği seçin
* Giden bağlantılar (Uzak Masaüstü İstemcisi): Geçerli NVDA örneği, bir veya
  daha fazla sunucuya bağlanan bir uzak masaüstü istemcisinde çalışıyorsa bu
  seçeneği seçin
* Güvenli Masaüstü geçişi: Güvenli masaüstüne erişirken NVDA'nın kullanıcı
  örneğinden Braille ve konuşma kullanmak istiyorsanız bu seçeneği
  belirleyin. Bunun çalışması için RDAccess eklentisini NVDA'nın güvenli
  masaüstü kopyasında kullanılabilir hale getirmeniz gerektiğini
  unutmayın. Bunun için NVDA'nın ayarlar Genel içerisinde "Oturum açma
  sırasında ve güvenli ekranlarda şu anda kayıtlı ayarları kullan (yönetici
  ayrıcalıkları gerektirir)" seçeneğini belirleyin.

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

Bu istemci seçeneği, etkinleştirildiğinde, uzak sistemden sürücü ayarlarını
(Sentezleyici sesi ve perdesi gibi) kontrol etmenize olanak tanır. Bu,
özellikle uzaktaki bir sistemi kontrol ederken yerel NVDA menüsüne erişimde
zorluk yaşıyorsanız kullanışlıdır. Uzak sistem üzerinde yapılan
değişiklikler otomatik olarak yerel olarak yansıtılacaktır.

Bu seçeneğin etkinleştirilmesi bir miktar performans düşüşü anlamına gelse
de, bunu etkinleştirmeniz tavsiye edilir. Bu seçenek devre dışı
bırakıldığında, büyük harfler için konuşma sentezleyici ses perdesi
değişiklikleri çalışmaz.

### NVDA kapatıldığında istemci desteğini sürdür

Bu istemci seçeneği yalnızca yüklü NVDA kopyalarında
mevcuttur. Etkinleştirildiğinde, NVDA çalışmıyorken bile NVDA'nın istemci
kısmının uzak masaüstü istemcinize yüklenmesini sağlar.

RDAccess'in istemci kısmını kullanmak için Windows Kayıt Defteri'nde birkaç
değişiklik yapılması gerekir. Eklenti, bu değişikliklerin mevcut
kullanıcının profili altında yapılmasını sağlar. Bu değişiklikler yönetici
ayrıcalıkları gerektirmez. Bu nedenle NVDA, yüklendiğinde gerekli
değişiklikleri otomatik olarak uygulayabilir ve NVDA'dan çıkarken bu
değişiklikleri geri alabilir. Bu, eklentinin NVDA'nın taşınabilir
sürümleriyle tamamen uyumlu olmasını sağlar.

Bu seçenek varsayılan olarak devre dışıdır. Ancak yüklü bir kopya
çalıştırıyorsanız ve sistemin tek kullanıcısı sizseniz bu seçeneği
etkinleştirmeniz önerilir. Bu, uzak bir sisteme bağlanırken NVDA'nın aktif
olmaması ve daha sonra başlatılması durumunda sorunsuz çalışmayı sağlar.

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
kitaplık olan [RD Pipe][4]'e dayanır. RD Pipe, Özgür Yazılım Vakfı
tarafından yayınlanan [GNU Affero Genel Kamu Lisansı sürüm 3][5] koşulları
kapsamında bu eklentinin bir parçası olarak yeniden dağıtılmaktadır.

[[!tag stable dev beta]]

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess

[3]: https://github.com/leonardder/rdAccess/issues

[4]: https://github.com/leonardder/rd_pipe-rs

[5]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
