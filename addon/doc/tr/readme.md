# RDAccess: Uzak Masaüstü Erişilebilirliği

* Authors: [Leonard de Ruijter][1]
* Download [latest stable version][2]
* NVDA uyumluluğu: 2026.1 ve üzeri

RDAccess eklentisi (Uzak Masaüstü Erişilebilirliği), NVDA'ya Microsoft Uzak Masaüstü, Citrix, Parallels RAS veya VMware Horizon uzak oturumları için destek ekler.
NVDA'da hem istemciye hem de sunucuya yüklendiğinde, sunucuda oluşturulan konuşma ve braille, istemci makinede braille olarak konuşulacak ve görüntülenecektir.
Bu, uzak bir sistemi yönetmenin, yerel sistemi çalıştırmak kadar kusursuz hissettirdiği bir kullanıcı deneyimi sağlar.

## Features

* Microsoft Uzak Masaüstü (Azure Sanal Masaüstü ve Microsoft Bulut PC dahil), Citrix, Parallels RAS ve VMware Horizon desteği
* Speech and braille output
* NVDA'nın otomatik braille ekran algılama özelliğini kullanarak uzaktan braille'in otomatik algılanması
* NVDA'nın ayarlar iletişim kutusunda devre dışı bırakılabilen özel bir algılama işlemi kullanılarak uzaktan konuşmanın otomatik algılanması
* NVDA'nın sunucuda çalışan taşınabilir kopyaları için destek (Citrix için ek yapılandırma gereklidir)
* Bir istemcide çalışan NVDA'nın taşınabilir kopyaları için tam destek (eklentiyi yüklemek için ek yönetici ayrıcalıklarına gerek yoktur)
* Aynı anda birden fazla aktif müşteri oturumu
* NVDA başlatıldıktan hemen sonra uzaktan masaüstü erişimi sağlanır
* Uzak oturumdan ayrılmadan belirli sentezleyici ve braille ekran ayarlarını kontrol edebilme

## Changelog

### Version 2.0.3

* Caps lock synchronization on the client now relies on NVDA 2026.3, which lets RDAccess tell caps lock presses fed back by the remote desktop client apart from real key presses. Synchronization therefore also works when the session is not full screen but Windows key combinations are applied on the remote computer, and when the NVDA setting "Handle keys from other applications" is disabled. The client side of the synchronization requires NVDA 2026.3 or later and is no longer available on older versions of NVDA; the server side keeps working on every supported version.

### Version 2.0.2

* Fixed caps lock going out of sync between the client and the server when both NVDA instances use caps lock as an NVDA modifier key. Quickly repeated caps lock presses in a full screen session no longer toggle caps lock on the client, and when caps lock is really toggled within the session, the client now follows as soon as the session loses focus. This behavior is controlled by the new setting "Synchronize the caps lock key between client and server", which is enabled by default and needs to be enabled on both the client and the server to work correctly. Note that with the setting "Handle keys from other applications" disabled on the client, caps lock can still get out of sync.

### Sürüm 2.0.1

* Uzaktan konuşma otomatik olarak açıldığında, artık bir konfigürasyon profili değişiminden sonra konuşmaya devam ediyor. Daha önce NVDA, bir profil etkinleştirildiğinde, örneğin kendi profili olan bir uygulamaya geçtiğinizde, yapılandırdığınız sentezleyiciye geri dönüyordu.
* "Bağlantı kaybından sonra uzaktan konuşmayı otomatik olarak kurtar" seçeneğinin adı, ne yaptığını daha iyi açıklayan "Mümkün olduğunda uzaktan konuşmaya otomatik olarak geç" olarak yeniden adlandırıldı.
* Uzak sentezleyiciyi kullanırken otomatik dil değiştirme etkinleştirildiğinde uzak sistemdeki sık görülen hatalar düzeltildi. Desteklenmeyen dillerin raporlanması artık istemcideki konuşma sentezleyici tarafından desteklenen dilleri yansıtıyor.
* Windows'un ARM64 sürümlerinde, x64 öykünmesi altında çalışan uzak masaüstü istemcileri artık Uzak Masaüstü Erişilebilirliği'ni kullanabilir.
* NVDA 2026.3'te tanıtılan braille girdi değişikliklerine uyarlanmıştır.

### Sürüm 2.0

* Uzak sistemden gelen konuşma ve braille artık daha erken sunuluyor, bu da uzak oturumda çalışmanın daha duyarlı olmasını sağlıyor.
* NVDA'nın uzak sunucu örneğini başlatırken, Braille artık ilk tuş vuruşundan veya odak değişikliğinden sonra değil, uzak oturum bağlandığı anda gösterilecektir.
* Bir oturumun bağlantısı kesilirken uzak sentezleyiciden veya braille ekranından geçiş yapıldığında meydana gelen donma düzeltildi.
* Uzak Masaüstü Erişilebilirliği artık NVDA'nın yerleşik Uzaktan Erişimi tarafından kullanılana benzer yeni bir protokol kullanarak konuşma ve braille alışverişi yapıyor. Daha sağlamdır ve artık güvenliği ihlal edilmiş bir uzak sistemin kötüye kullanabileceği turşu formatına bağlı değildir. Protokol sürümü otomatik olarak seçilir, böylece RDAccess'in farklı sürümlerini çalıştıran istemci ve sunucu birlikte çalışmaya devam eder.
* Minimum uyumlu NVDA sürümü artık 2026.1'dir. Önceki sürümler için destek kaldırıldı.
* NVDA 2026.3'te sunulan braille değişikliklerine uyarlanmıştır.
* RD Pipe bağımlılığı 0.9.0 sürümüne güncellendi.
* Uzak Masaüstü Erişilebilirliği artık GNU Genel Kamu Lisansı sürüm 2 veya üzeri kapsamında lisanslanmıştır.

### Sürüm 1.7.1

* Umarız rd_pipe'ta yanlış sanal kanalın oluşturulmasına neden olan bir hata düzeltilmiştir.

### Sürüm 1.7

* Güvenli masaüstü desteği kaldırıldı.
* Uzak bir NVDA'dan iletilen konuşmanın perdesini değiştirmek için "Gelen konuşma perdesi değişim yüzdesi" istemci seçeneği eklendi, böylece uzak ve yerel konuşma duyulabilir şekilde ayırt edilebilir hale getirildi.

### Sürüm 1.6

* Belgelenmiş ve geliştirilmiş Parallels RAS desteği.
* Minimum uyumlu NVDA sürümü artık 2025.1'dir. Önceki sürümler için destek kaldırıldı.
* RdPipe bağımlılığı güncellendi.
* RdPipe günlük düzeyini yapılandırma yeteneği eklendi.
* Ayarlar panelinde RdPipe günlüğü için bir görüntüleyici eklendi.
* İyileştirilmiş kaldırma davranışı (Citrix kullanılamadığında artık hatalara neden olmuyor veya Citrix desteğini kaldırmıyor).

### Version 1.5

* Uzak Masaüstü Erişilebilirliği ayarları panelindeki [#23](https://github.com/leonardder/rdAccess/pull/23) bir düğme aracılığıyla hata ayıklama tanılama raporu oluşturma yeteneğini ekleyin.
* NVDA 2025.1 ve daha yeni sürümlerde [#19](https://github.com/leonardder/rdAccess/pull/13) çok satırlı braille ekran desteği.
* Minimum uyumlu NVDA sürümü artık 2024.1'dir. Önceki sürümler için destek kaldırıldı.
* İstemci bağlantı bildirimleri eklendi [#25](https://github.com/leonardder/rdAccess/pull/25).
* RdPipe bağımlılığı güncellendi.
* Çeviriler güncellendi.

### Version 1.4

* Yeni kararlı sürüm yayınlandı.

### Version 1.3

* Kırık braille ekran hareketleri düzeltildi.

### Version 1.2

* Biçimlendirici ve linter olarak [Ruff](https://github.com/astral-sh/ruff) kullanın. [#13](https://github.com/leonardder/rdAccess/pull/13).
* İstemcideki NVDA'nın, sunucudaki konuşmayı duraklatırken hata oluşturması sorunu düzeltildi.
* 'winAPI.secureDesktop.post_secureDesktopStateChange' desteği düzeltildi.
* Sunucuda iyileştirilmiş sürücü başlatma.

### Version 1.1

* Braille ekranlarının otomatik algılanması için NVDA 2023.3 tarzı cihaz kaydı desteği eklendi. [#11](https://github.com/leonardder/rdAccess/pull/11).
* NVDA 2024.1 Alpha `winAPI.secureDesktop.post_secureDesktopStateChange` uzantı noktası desteği eklendi. [#12](https://github.com/leonardder/rdAccess/pull/12).

### Version 1.0

İlk Kararlı sürüm.

## Getting Started

1. Uzak Masaüstü Erişilebilirliği'ni NVDA'nın hem istemci hem de sunucu kopyasına yükleyin.
1. Uzak sistem, yerel konuşma sentezleyiciyi kullanarak otomatik olarak konuşmaya başlamalıdır.
   Değilse, sunucudaki NVDA örneğinde, NVDA'nın sentezleyici seçim iletişim kutusundan uzak konuşma sentezleyiciyi seçin.
1. Braille'i kullanmak için, braille ekran seçim iletişim kutusunu kullanarak otomatik braille ekran algılamayı etkinleştirin.

## Configuration

Kurulumdan sonra Uzak Masaüstü Erişilebilirliği eklentisi, NVDA Menüsünden Tercihler > Ayarlar... seçeneğini seçerek erişilebilen NVDA'nın ayarlar iletişim kutusu kullanılarak yapılandırılabilir.
Ardından Uzak Masaüstü kategorisini seçin.

Bu iletişim kutusu aşağıdaki Ayarları içerir:

### Uzak Masaüstü Erişilebilirliğini Etkinleştir

Bu onay kutuları listesi eklentinin çalışma modunu kontrol eder.
Şunlardan birini seçin:

* Gelen bağlantılar (Uzak Masaüstü Sunucusu): NVDA'nın geçerli örneği bir uzak masaüstü sunucusunda çalışıyorsa bu seçeneği seçin.
* Giden bağlantılar (Uzak Masaüstü İstemcisi): NVDA'nın geçerli örneği bir veya daha fazla sunucuya bağlanan bir uzak masaüstü istemcisinde çalışıyorsa bu seçeneği seçin.

Eklentiyle sorunsuz bir başlangıç ​​sağlamak için tüm seçenekler varsayılan olarak etkindir.
Ancak uygun şekilde sunucu veya istemci modunu devre dışı bırakmanız önerilir.

### Büyük Harf Kilidi Tuşunu İstemci ve Sunucu arasında senkronize edin

When both the client and the server run NVDA with caps lock as an NVDA modifier key, the caps lock state can get out of sync, since the remote desktop client feeds caps lock presses back into the client system whenever it captures the keyboard, for example in a full screen session.
When this option is enabled on the client, these fed back caps lock presses no longer toggle caps lock on the client.
Sunucuda etkinleştirildiğinde, sunucu büyük harf kilidi durumunu istemciye bildirir ve uzak oturum odağı kaybettiğinde istemci bu durumu uygular.
Doğru davranış için bu seçeneğin hem istemcide hem de sunucuda etkinleştirilmesi gerekir; her ikisinde de varsayılan olarak etkindir.
On the client, this option requires NVDA 2026.3 or later; the server side works with every NVDA version supported by the add-on.

Note that while a remote desktop session window has focus, caps lock presses sent by other software, such as NVDA Remote Access, are suppressed on the client as well.

### Kullanılabilir Olduğunda Otomatik Olarak Uzaktan Konuşmaya Geç

Bu seçenek yalnızca sunucu modunda kullanılabilir.
Braille ekranın otomatik algılamasına benzer şekilde, Uzak Masaüstü istemcisi sunduğu anda Uzaktan Konuşmanın etkinleştirilmesini ve bağlantı kesildiğinde bağlantının otomatik olarak yeniden kurulmasını sağlar.
Uzaktan Konuşma bu şekilde etkinken, yapılandırılmış sentezleyicinize dokunulmaz ve yapılandırma profilleri arasında geçiş yapmak artık ona düşmez.

Bu seçenek varsayılan olarak etkinleştirilmiştir.
Uzak Masaüstü sunucusunda ses çıkışı yoksa bu seçeneğin etkin bırakılması önemle tavsiye edilir.

### Allow Remote System to Control Driver Settings

İstemcide etkinleştirildiğinde bu seçenek, uzak sistemden sürücü ayarlarını (synthesizer sesi ve perdesi gibi) kontrol etmenize olanak tanır.
Uzak sistemde yapılan değişiklikler otomatik olarak yerel olarak yansıtılacaktır.

### NVDA'dan Çıkarken Müşteri Desteğini Sürdürme

NVDA'nın yüklü kopyalarında bulunan bu istemci seçeneği, NVDA çalışmıyorken bile NVDA'nın istemci bölümünün uzak masaüstü istemcinize yüklenmesini sağlar.

RDAccess'in istemci kısmını kullanmak için Windows Kayıt Defteri'nde değişiklik yapılması gerekir.
Eklenti, bu değişikliklerin mevcut kullanıcının profili altında yapılmasını ve herhangi bir yönetici ayrıcalığı gerektirmemesini sağlar.
Bu nedenle NVDA, yüklendiğinde gerekli değişiklikleri otomatik olarak uygulayabilir ve NVDA'dan çıkarken bu değişiklikleri geri alabilir, böylece NVDA'nın taşınabilir sürümleriyle uyumluluk sağlanır.

Bu seçenek varsayılan olarak devre dışıdır.
Ancak yüklü bir kopya çalıştırıyorsanız ve sistemin tek kullanıcısıysanız, NVDA başladıktan sonra uzaktaki bir sisteme bağlanırken sorunsuz çalışma için bu seçeneği etkinleştirmeniz önerilir.

### Varsayılan Uzak Masaüstü Desteğini Etkinleştir

Varsayılan olarak etkin olan bu seçenek, NVDA başlatılırken Uzak Masaüstü Erişilebilirliği'nin istemci bölümünün Microsoft Uzak Masaüstü istemcisine (mstsc) yüklenmesini sağlar.
Bu aynı zamanda VMware Horizon, Parallels RAS, Azure Sanal Masaüstü için de gereklidir. vesaire.
Bu seçenek aracılığıyla yapılan değişiklikler, kalıcı istemci desteği etkinleştirilmediği sürece NVDA'dan çıkıldığında otomatik olarak geri alınacaktır.

### Citrix Workspace Desteğini Etkinleştir

Varsayılan olarak etkin olan bu seçenek, NVDA başlatılırken Uzak Masaüstü Erişilebilirliği'nin istemci kısmının Citrix Workspace uygulamasına yüklenmesini sağlar.
Bu seçenek aracılığıyla yapılan değişiklikler, kalıcı istemci desteği etkinleştirilmediği sürece NVDA'dan çıkıldığında otomatik olarak geri alınacaktır.

Bu seçenek yalnızca aşağıdaki koşullar altında kullanılabilir:

* Citrix Workspace kuruldu.
  Uygulamanın Windows Mağazası sürümünün, uygulamanın kendisindeki sınırlamalar nedeniyle desteklenmediğini unutmayın.
* Uzak Masaüstü Erişilebilirliği'ni geçerli kullanıcı bağlamı altında kaydetmek mümkündür.
  Uygulamayı yükledikten sonra bunu etkinleştirmek için bir kez uzaktan oturum başlatmanız gerekir.

### Notify of connection changes with

Bu birleşik giriş kutusu, uzak bir sistem uzak konuşma veya braille bağlantısını açtığında veya kapattığında alınan bildirimleri kontrol etmenize olanak tanır.
Aşağıdakiler arasında seçim yapabilirsiniz:

* Kapalı (Bildirim yok)
* Mesajlar (ör. "Uzaktan Braille bağlı")
* Sounds
* Both messages and sounds

### Gelen Konuşma Perdesi Değişim Yüzdesi

Bu istemci seçeneği, uzak bir NVDA'dan geldiğinde yerel olarak oluşturulan konuşmanın perdesini değiştirerek, uzak ve yerel konuşmayı duyulabilir şekilde ayırt edilebilir hale getirir.

Değer -100 ile 100 arasında bir yüzdedir.
Pozitif değerler perdeyi yükseltir, negatif değerler ise düşürür.
0 değeri kaydırmayı devre dışı bırakır.
Varsayılan 10'dur.

Kaydırma yalnızca yerel sentezleyici perde komutlarını desteklediğinde uygulanır; Perde desteği olmayan sentezleyiciler etkilenmez.

### Open diagnostics report

Bu düğme, muhtemelen hata ayıklamaya yardımcı olabilecek çeşitli tanılamalar içeren JSON çıktısına sahip, göz atılabilir bir ileti açar.
[GitHub'da bir sorun bildirirken][4], bu raporu sağlamanız istenebilir.

## Citrix'e Özel Talimatlar

Uzak Masaüstü Erişilebilirliği'ni Citrix Workspace uygulamasıyla kullanırken dikkat edilmesi gereken önemli noktalar vardır:

### İstemci Tarafı Gereksinimleri

1. Uygulamanın Windows Mağazası sürümü *desteklenmemektedir*.
1. Citrix Workspace'i yükledikten sonra, Uzak Masaüstü Erişilebilirliği'nin kendisini kaydetmesine izin vermek için bir kez uzak oturum başlatmanız gerekir.
   Bunun nedeni, uygulamanın ilk oturum kurulumu sırasında sistem ayarlarını kullanıcı ayarlarına kopyalamasıdır.
   Bunu takiben Uzak Masaüstü Erişilebilirliği kendisini geçerli kullanıcı bağlamı altında kaydedebilir.

### Sunucu Tarafı Gereksinimi

Citrix Virtual Apps and Desktops 2109'da Citrix, varsayılan olarak Uzak Masaüstü Erişilebilirliği'nin gerektirdiği kanal da dahil olmak üzere üçüncü taraf sanal kanallarını kısıtlayan sanal kanal izin verilenler listesini etkinleştirdi.
Daha fazla bilgi için [bu Citrix blog gönderisine bakın](https://www.citrix.com/blogs/2021/10/14/virtual-channel-allow-list-now-enabled-by-default/).

Uzak Masaüstü Erişilebilirliği'nin gerektirdiği RdPipe kanalına açıkça izin verilmesi henüz test edilmemiştir.
Şimdilik izin verilenler listesini tamamen devre dışı bırakmak en iyisidir.
Sistem yöneticinizin endişeleri varsa, [sorunu burada ele almaktan] çekinmeyin[3].

## Sorunlar ve Katkıda Bulunmak

Bir sorunu bildirmek veya katkıda bulunmak için [Github'daki sorunlar sayfasına][4] bakın.

## Harici Bileşenler

Bu eklenti, uzak masaüstü istemci desteğini destekleyen, Rust'ta yazılmış bir kitaplık olan [RD Pipe][5]'a dayanır.
RD Pipe, bu eklentinin bir parçası olarak [GNU Affero Genel Kamu Lisansı'nın 3. sürümü] koşulları kapsamında yeniden dağıtılmaktadır.

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess

[3]: https://github.com/leonardder/rdAccess/issues/1

[4]: https://github.com/leonardder/rdAccess/issues

[5]: https://github.com/leonardder/rd_pipe-rs

[6]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
