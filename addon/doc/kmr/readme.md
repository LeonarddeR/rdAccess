# RDAccess: Gihîştina Sermaseya Dûr

* Nivîskar: [Leonard de Ruijter][1]
* Dakêşana [guhertoya herî dawî ya aram] [2]
* Lihevhatina NVDA: 2026.1 û paşê

Pêveka RDAccess (Remote Desktop Gihîştinî) piştgirîyê ji bo danişînên dûr ên Microsoft Remote Desktop, Citrix, Parallels RAS, an VMware Horizon li NVDA zêde dike.
Dema ku di NVDA de hem li ser xerîdar û hem jî li ser serverê were sazkirin, axaftin û braille-a li ser serverê hatî çêkirin dê li ser makîneya xerîdar bi braille were axaftin û xuyang kirin.
Ev ezmûnek bikarhêner peyda dike ku tê de birêvebirina pergalek ji dûr ve bi qasî xebitandina pergala herêmî bêkêmasî be.

## Taybetmendî

* Piştgiriya ji bo Microsoft Remote Desktop (tevî Azure Virtual Desktop û Microsoft Cloud PC), Citrix, Parallels RAS, û VMware Horizon
* Derana axaftinê û braille
* Tesbîtkirina otomatîkî ya braille ya ji dûr ve bi karanîna tesbîtkirina otomatîkî ya dîmendera braille ya NVDA-yê
* Tesbîtkirina otomatîkî ya axaftina ji dûr ve bi karanîna pêvajoyek tesbîtkirinê ya taybetî ku dikare di diyaloga mîhengên NVDA de were neçalak kirin.
* Piştgiriya kopiyên veguhêzbar ên NVDA-yê yên ku li ser serverekê dixebitin (ji bo Citrix-ê mîhengkirina zêde hewce ye)
* Piştgiriya tevahî ji bo kopiyên veguhêzbar ên NVDA-yê yên ku li ser xerîdar dixebitin (ji bo sazkirina pêvekê mafên rêveberiyê yên zêde ne hewce ne)
* Çend danişînên çalak ên xerîdar di heman demê de
* Sermaseya dûr yekser piştî destpêkirina NVDA-yê peyda dibe.
* Şîyana kontrolkirina mîhengên taybetî yên sentezator û dîmendera braille bêyî derketina ji danişîna dûr

## Guhertinname

### Version 2.0.3

* Caps lock synchronization on the client now relies on NVDA 2026.3, which lets RDAccess tell caps lock presses fed back by the remote desktop client apart from real key presses. Synchronization therefore also works when the session is not full screen but Windows key combinations are applied on the remote computer, and when the NVDA setting "Handle keys from other applications" is disabled. The client side of the synchronization requires NVDA 2026.3 or later and is no longer available on older versions of NVDA; the server side keeps working on every supported version.

### Version 2.0.2

* Fixed caps lock going out of sync between the client and the server when both NVDA instances use caps lock as an NVDA modifier key. Quickly repeated caps lock presses in a full screen session no longer toggle caps lock on the client, and when caps lock is really toggled within the session, the client now follows as soon as the session loses focus. This behavior is controlled by the new setting "Synchronize the caps lock key between client and server", which is enabled by default and needs to be enabled on both the client and the server to work correctly. Note that with the setting "Handle keys from other applications" disabled on the client, caps lock can still get out of sync.

### Versiyon 2.0.1

* Dema ku axaftina ji dûr ve bixweber tê vekirin, ew êdî piştî guhertina profîla mîhengkirinê jî diaxive. Berê, NVDA vedigeriya sentezatorê ku we mîheng kiribû gava profîlek dihat çalakkirin, mînakî dema ku hûn diçûn serîlêdanek bi profîla wê.
* Navê vebijarka "Piştî windabûna pêwendiyê axaftina dûr bixweber sererast bike" bo "Dema ku hebe bixweber bizivire axaftina dûr", ku çêtir rave dike ka ew çi dike.
* Çewtiyên dubare yên li ser pergala dûr hatin rastkirin dema ku guheztina otomatîk a zimanan di dema karanîna sentezatorê dûr de çalak bû. Raporkirina zimanên ku nayên piştgirîkirin niha zimanên ku ji hêla sentezatorê axaftinê ve li ser xerîdar têne piştgirî kirin nîşan dide.
* Li ser guhertoyên ARM64 yên Windows-ê, xerîdarên sermaseya dûr ên ku di bin emulasyona x64 de dixebitin naha dikarin RDAccess bikar bînin.
* Li gorî guhertinên têketina braille yên ku di NVDA 2026.3 de hatine destnîşan kirin hatî adaptekirin.

### Versiyon 2.0

* Axaftin û Braille ji pergala dûr ve niha zûtir têne pêşkêş kirin, ev yek jî xebata di danişînek dûr de bersivdayînek çêtir dide hîskirin.
* Dema ku nimûneyek serverek dûr a NVDA tê destpêkirin, braille niha hema ku danişînek dûr ve girêdayî dibe tê nîşandan, li şûna tenê piştî tikandina yekem a bişkokê an guhertina fokusê.
* Dema ku danişîn qut dibû, cemidandinek hate rastkirin dema ku meriv ji sentezatorê dûr an jî dîmendera braille dûr diket.
* Niha RDAccess bi karanîna protokoleke nû ya ku li gorî protokola ku ji hêla Remote Access ya çêkirî ya NVDA ve hatî modelkirin, axaftin û Braille diguhezîne. Ew xurttir e û êdî bi formata pickle ve girêdayî nîne ku pergaleke dûr a xeternak dikare îstismar bike. Guhertoya protokolê bixweber tê hilbijartin, ji ber vê yekê xerîdar û serverek ku guhertoyên cûda yên RDAccess dimeşînin hîn jî bi hev re dixebitin.
* Kêmtirîn guhertoya NVDA ya lihevhatî niha 2026.1 e. Piştgiriya ji bo guhertoyên berê hatiye rakirin.
* Li gorî guhertinên braille yên ku di NVDA 2026.3 de hatine destnîşan kirin hatîye adaptekirin.
* Girêdayîbûna RD Pipe bo guhertoya 0.9.0 hate nûve kirin.
* RDAccess niha di bin Lîsansa Giştî ya Giştî ya GNU versiyon 2 an jî nûtir de lîsanskirî ye.

### Versiyon 1.7.1

* Hêvîdarim çewtiyek di rd_pipe de ku bû sedema çêkirina kanala virtual a xelet, hatibe çareserkirin.

### Versiyon 1.7

* Piştgiriya sermaseya ewle hate rakirin.
* Vebijarkek xerîdar a "Ji sedî guhertina bilindahiya axaftina hatî" hate zêdekirin da ku bilindahiya axaftina ji NVDA-yek dûr ve were pêşkêş kirin biguhezîne, axaftina dûr û ya herêmî bi awayekî bihîstbar ji hev were cudakirin.

### Versiyon 1.6

* Piştgiriya Parallels RAS ya belgekirî û başkirî.
* Kêmtirîn guhertoya NVDA ya lihevhatî niha 2025.1 e. Piştgiriya ji bo guhertoyên berê hatiye rakirin.
* Girêdayîbûna RdPipe-ê nûvekirî.
* Şîyana mîhengkirina asta têketina RdPipe zêde kir.
* Temaşevanek ji bo têketina RdPipe zêde kir, ku ji panela mîhengan peyda dibe.
* Reftara rakirinê ya baştirkirî (êdî xeletiyan dernaxe an piştgiriya Citrix-ê ranake dema ku Citrix peyda nebe).

### Versiyon 1.5

* Bi rêya bişkokekê di panela mîhengên RDAccess de [#23](https://github.com/leonardder/rdAccess/pull/23 ) şiyana çêkirina raporek teşhîsa xeletkirina çewtiyan zêde bike.
* Piştgiriya ji bo dîmenderên braille yên pir-rêzik di NVDA 2025.1 û nûtir de [#19](https://github.com/leonardder/rdAccess/pull/13).
* Kêmtirîn guhertoya NVDA ya lihevhatî niha 2024.1 e. Piştgiriya ji bo guhertoyên berê hatiye rakirin.
* Agahdariyên girêdana xerîdar lê zêde kirin [#25](https://github.com/leonardder/rdAccess/pull/25).
* Girêdayîbûna RdPipe-ê nûvekirî.
* Wergerên nûvekirî.

### Versiyon 1.4

* Guhertoya nû ya stabîl.

### Versiyon 1.3

* Jestên ekrana Braille yên şikestî hatin sererastkirin.

### Versiyon 1.2

* [Ruff](https://github.com/astral-sh/ruff) wekî formatker û lînter bikar bînin. [#13](https://github.com/leonardder/rdAccess/pull/13).
* Pirsgirêkek çareser kir ku tê de NVDA li ser xerîdar dema rawestandina axaftinê li ser serverê çewtiyek çêdikir.
* Piştgiriya ji bo `winAPI.secureDesktop.post_secureDesktopStateChange` hate rastkirin.
* Destpêkirina ajokerê li ser serverê baştir kir.

### Versiyon 1.1

* Piştgiriya qeydkirina cîhaza bi şêwaza NVDA 2023.3 ji bo tespîtkirina otomatîkî ya dîmenderên braille hate zêdekirin. [#11](https://github.com/leonardder/rdAccess/pull/11).
* Piştgiriya ji bo xala dirêjkirinê ya NVDA 2024.1 Alpha `winAPI.secureDesktop.post_secureDesktopStateChange` hate zêdekirin. [#12](https://github.com/leonardder/rdAccess/pull/12).

### Versiyon 1.0

Guhertoya destpêkê ya stabîl.

## Destpêkirin

1. RDAccess li ser hem kopiyên xerîdar û hem jî yên serverê yên NVDA saz bike.
1. Divê pergala dûr bi karanîna sentezatorê axaftina herêmî bixweber dest bi axaftinê bike.
   Eger ne wisa be, di mînaka NVDA ya li ser serverê de, sentezatorê axaftinê yê ji dûr ve ji diyaloga hilbijartina sentezatorê NVDAyê hilbijêre.
1. Ji bo bikaranîna Braille, tespîtkirina otomatîk a dîmendera Braille bi karanîna diyaloga hilbijartina dîmendera Braille çalak bike.

## Mîhengkirin

Piştî sazkirinê, pêveka RDAccess dikare bi karanîna diyaloga mîhengên NVDA-yê were mîheng kirin, ku ji Menuya NVDA-yê bi hilbijartina Tercîh > Mîheng... ve tê gihîştin.
Dûv re, kategoriya Remote Desktop hilbijêrin.

Ev diyalog mîhengên jêrîn dihewîne:

### Gihîştina Sermaseya Dûr çalak bike ji bo

Ev lîsteya qutiyên kontrolê moda xebitandinê ya pêvekê kontrol dike.
Hilbijêre di navbera:

* Girêdanên Hatî (Serverê Sermaseya Dûr): Heke mînaka heyî ya NVDA li ser serverek sermaseya dûr dixebite, vê vebijarkê hilbijêrin.
* Girêdanên Derketî (Muwekîlê Sermaseya Dûr): Heke mînaka heyî ya NVDA li ser muwekîlek sermaseya dûr dixebite ku bi yek an çend serveran ve girêdide, vê vebijarkê hilbijêrin.

Ji bo ku destpêkek xweş bi pêvekê re were misoger kirin, hemî vebijark bi xwerû têne çalak kirin.
Lêbelê, tê pêşniyar kirin ku hûn moda server an xerîdar li gorî rewşê neçalak bikin.

### Bişkojka Caps Lock di navbera Xerîdar û Serverê de senkronîze bike

When both the client and the server run NVDA with caps lock as an NVDA modifier key, the caps lock state can get out of sync, since the remote desktop client feeds caps lock presses back into the client system whenever it captures the keyboard, for example in a full screen session.
When this option is enabled on the client, these fed back caps lock presses no longer toggle caps lock on the client.
Dema ku li ser serverê çalak be, server rewşa caps lock-a xwe ji xerîdar re radigihîne, ku ew jî wê gava ku danişîna dûr balê winda dike, bicîh tîne.
Ji bo tevgereke rast, divê ev vebijêrk hem li ser xerîdar û hem jî li ser serverê çalak be; ew bi xwerû li ser herduyan jî çalak e.
On the client, this option requires NVDA 2026.3 or later; the server side works with every NVDA version supported by the add-on.

Note that while a remote desktop session window has focus, caps lock presses sent by other software, such as NVDA Remote Access, are suppressed on the client as well.

### Dema ku peyda bibe, bixweber biguhere ser axaftina ji dûr ve

Ev vebijêrk tenê di moda serverê de heye.
Ew piştrast dike ku Axaftina Ji Dûr ve hema ku xerîdarek sermaseya dûr pêşkêş dike tê çalak kirin, mîna tespîtkirina otomatîk a dîmendera braille, û ku girêdan dema ku winda dibe bixweber ji nû ve tê saz kirin.
Her çiqas Axaftina Ji Dûr bi vî rengî çalak be jî, sentezatorê we yê mîhengkirî bê dest lê nayê dayîn, û guheztina profîlên mîhengkirinê êdî venagere ser wê.

Ev vebijêrk bi xwerû çalak e.
Ger pêşkêşkara Dûr-Masketeyê derana deng tune be, bi tundî tê pêşniyar kirin ku ev vebijark çalak bimîne.

### Destûrê bide Pergala Ji Dûr ve ku Mîhengên Ajokar Kontrol Bike

Dema ku di xerîdar de çalak be, ev vebijêrk dihêle hûn mîhengên ajokerê (wek dengê sentezator û bilindahiya wê) ji pergala dûr ve kontrol bikin.
Guhertinên ku li ser pergala dûr hatine çêkirin dê bixweber li herêmê werin nîşandan.

### Dema Derketina ji NVDA Piştgiriya Xerîdar Berdewam Bike

Ev vebijarka xerîdar, ku li ser kopiyên sazkirî yên NVDA-yê peyda dibe, piştrast dike ku beşa xerîdar a NVDA-yê di xerîdara sermaseya we ya dûr de tê barkirin, tewra dema ku NVDA nexebite jî.

Ji bo bikaranîna beşa xerîdar a RDAccess, divê guhertin di Registry ya Windows-ê de werin kirin.
Ev pêvek piştrast dike ku ev guhertin di bin profîla bikarhênerê heyî de têne kirin, û hewcedariya wan bi mafên rêveberiyê tune.
Ji ber vê yekê, NVDA dikare dema ku tê barkirin guhertinên pêwîst bixweber bicîh bîne û dema ku ji NVDA derdikeve van guhertinan betal bike, bi vî awayî hevahengiya bi guhertoyên veguhêzbar ên NVDA re misoger dike.

Ev vebijêrk bi xwerû neçalak e.
Lêbelê, heke hûn kopiyek sazkirî dimeşînin û hûn tenê bikarhênerê pergalê ne, tê pêşniyar kirin ku hûn vê vebijarkê çalak bikin da ku piştî destpêkirina NVDA-yê dema ku hûn bi pergalek dûr ve girêdayî dibin, xebata bêkêmasî bikin.

### Piştgiriya Sermaseya Dûr a Xwerû Çalak Bike

Ev vebijêrk, ku bi xweberî çalak e, piştrast dike ku beşa xerîdar a RDAccess di dema destpêkirina NVDA de di xerîdarê Microsoft Remote Desktop (mstsc) de tê barkirin.
Ev ji bo VMware Horizon, Parallels RAS, Azure Virtual Desktop û hwd jî pêdivî ye.
Guhertinên ku bi rêya vê vebijarkê têne çêkirin dê dema derketina ji NVDA bixweber werin betalkirin heya ku piştgiriya xerîdar a domdar neyê çalak kirin.

### Piştgiriya Citrix Workspace çalak bike

Ev vebijêrk, ku bi xweberî çalak e, piştrast dike ku beşa xerîdar a RDAccess dema destpêkirina NVDA di sepana Citrix Workspace de tê barkirin.
Guhertinên ku bi rêya vê vebijarkê têne çêkirin dê dema derketina ji NVDA bixweber werin betalkirin heya ku piştgiriya xerîdar a domdar neyê çalak kirin.

Ev vebijêrk tenê di bin şert û mercên jêrîn de heye:

* Citrix Workspace hatiye sazkirin.
  Ji kerema xwe bala xwe bidinê ku guhertoya Windows Store ya sepanê ji ber sînorkirinên di sepanê de bi xwe nayê piştgirîkirin.
* Qeydkirina RDAccess di çarçoveya bikarhênerê heyî de gengaz e.
  Piştî sazkirina sepanê, ji bo çalakkirina vê yekê divê hûn carekê danişînek ji dûr ve bidin destpêkirin.

### Agahdariya guhertinên girêdanê bi

Ev qutiya kombo dihêle hûn agahdariyên ku dema pergalek ji dûr ve pêwendiya axaftinê an Braille ya ji dûr ve vedike an digire, kontrol bikin.
Tu dikarî di navbera wan de hilbijêrî:

* Girtî (Agahdarî tune)
* Peyam (mînak "Braille ji dûr ve girêdayî ye")
* Sounds
* Hem peyam û hem jî deng

### Rêjeya Guhertina Bilindahiya Axaftina Hatî

Ev vebijarka xerîdar dema ku ji NVDA-yek dûr tê, bilindahiya axaftina ku bi awayekî herêmî tê pêşkêş kirin diguherîne, û ev yek axaftina dûr û herêmî bi awayekî bihîstbar ji hev vediqetîne.

Nirx rêjeyek di navbera -100 û 100 de ye.
Nirxên erênî tona deng bilind dikin, nirxên neyînî jî kêm dikin.
Nirxa 0 shiftê neçalak dike.
Nirxa xwerû 10 e.

Guhertin tenê dema ku sentezatorê herêmî fermanên pitch piştgirî dike tê sepandin; sentezatorên bêyî piştgiriya pitch bêbandor in.

### Rapora teşhîsê veke

Ev bişkok peyameke gerokî bi derana JSON vedike ku çend teşhîsan dihewîne ku dibe ku di çareserkirina çewtiyan de bibin alîkar.
Dema ku [pirsgirêkek li GitHubê tomar dikî][4], dibe ku ji we were xwestin ku hûn vê raporê peyda bikin.

## Rênimayên Taybetî yên Citrix

Dema ku hûn RDAccess bi sepana Citrix Workspace re bikar tînin, xalên girîng hene ku divê werin zanîn:

### Pêdiviyên Alîyê Xerîdar

1. Guhertoya Windows Store ya sepanê *nayê* piştgirîkirin.
1. Piştî sazkirina Citrix Workspace, divê hûn carekê danişînek ji dûr ve bidin destpêkirin da ku RDAccess xwe qeyd bike.
   Ev ji ber wê yekê diqewime ku bername di dema sazkirina rûniştina destpêkê de mîhengên pergalê li mîhengên bikarhêner kopî dike.
   Piştî vê yekê, RDAccess dikare xwe di bin çarçoveya bikarhênerê heyî de tomar bike.

### Pêdiviya Alîyê Serverê

Di Citrix Virtual Apps and Desktops 2109 de, Citrix-ê navnîşa destûrdayî ya kanalên virtual çalak kir, û kanalên virtual ên partiya sêyemîn, tevî kanala ku ji hêla RDAccess ve tê xwestin, bi xweber sînordar kir.
Ji bo bêtir agahdarî, [li vê posta bloga Citrix binêre](https://www.citrix.com/blogs/2021/10/14/virtual-channel-allow-list-now-enabled-by-default/).

Destûrdayîna eşkere ya kanala RdPipe ya ku ji hêla RDAccess ve tê xwestin hîn nehatiye ceribandin.
Ji bo niha, çêtirîn e ku navnîşa destûrnameyê bi tevahî were neçalak kirin.
Heke rêveberê sîstema we fikarên we hebin, ji kerema xwe [pirsgirêkê li vir çareser bikin][3].

## Pirsgirêk û Beşdarbûn

Ji bo ragihandina pirsgirêkekê an beşdarbûnê, li [rûpela pirsgirêkan li ser Github][4] binêre.

## Pêkhateyên Derveyî

Ev pêvek xwe dispêre [RD Pipe][5], pirtûkxaneyek ku bi Rust hatiye nivîsandin û piştgiriya xerîdarê sermaseya dûr dike.
RD Pipe wekî beşek ji vê pêvekê li gorî şertên [guhertoya 3-an a Lîsansa Giştî ya GNU Affero][6] ji nû ve tê belavkirin.

[1]: https://github.com/leonardder/

[2]: https://www.nvaccess.org/addonStore/legacy?file=rdAccess

[3]: https://github.com/leonardder/rdAccess/issues/1

[4]: https://github.com/leonardder/rdAccess/issues

[5]: https://github.com/leonardder/rd_pipe-rs

[6]: https://github.com/leonardder/rd_pipe-rs/blob/master/LICENSE
