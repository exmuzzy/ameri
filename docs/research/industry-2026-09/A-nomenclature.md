# A. Номенклатура ПП-вентиляции: синонимы, обозначения, покупные позиции

Исследование для словаря разбора спецификаций (харнес ameri, `harness/duct_calc/`). Дата обращения ко всем источникам — **2026-09-26**.

Как читать пометки:
- **(не проверено)** — факт взят из выдачи поиска или вторичного источника, первоисточник не открыт; либо термин в источниках не найден.
- **(форум)** — так пишут на практике, по данным форума проектировщиков.
- **(вывод)** — наш анализ по найденным фактам, не цитата.
- **(внутр.)** — строки клиентов из задания и действующие правила харнеса (`parse_rules.md`, `params.yaml`).

Главный первичный источник по ПП — каталог и сайт «Спецвент» (СПб): там есть формат обозначений с кодами соединений. Остальные производители (ПластПлэнт, Полимеризделия, Тетра, POLEX, Ватер Групп, Полиюнион, УралАктив, Plast Product, SPB Active) подтверждают номенклатуру. Зарубежные термины взяты из каталогов KWERK, SR Kunststofftechnik, FRANK (DE), Simtech и Asahi/America (США), XICHENG (Китай).

---

## 0. Главное

1. **«короб» в списке покупных у прототипа опасен.** У производителей ПП «короб» — это сам воздуховод: «Трубы и короба из полипропилена», «пластиковые воздуховоды (короба)» ([ПластПлэнт](https://plastplant.ru/plastikovye-vozduhovody/)), «металлические короба» ([Полимеризделия](https://izpolimera.ru/vozduhovodi-polipropilen/)). Строка «Короб ПП 600х300» уйдёт в покупные.
2. **Подстрока «вентилятор» ловит описания чужих позиций:** «Защитная сетка ⌀250 (входное сечение вентилятора)» (внутр.), «Переход … к вентилятору» (вывод). Проверь в прототипе, что `grid_keywords` проверяются раньше покупных. Другой вариант — считать строку покупной, только если слово стоит в начале наименования.
3. **«клапан» добавлять нельзя.** Дроссель-клапаны, обратные и перекидные клапаны, шиберы из ПП производители делают сами ([Спецвент](https://specvent.com/katalog.html), [Полимеризделия](https://izpolimera.ru/vozduhovodi-polipropilen/), [SPB Active](http://spbactive.ru/production/airducts/)). Покупные клапаны ловим по маркам и признакам: КВР, КПУ, КЛОП, «огнезадерж», «противопожар», Belimo.
4. **«электропривод» — смешанная позиция.** «Дроссель-клапан ПП-ЭП 560-Ф» — это ПП-клапан «с площадкой под электропривод» ([Спецвент](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/drossel-klapany-s-elektroprivodom.html)). Корпус свой, привод покупной. Решает руководитель.
5. **ФВГ — «фильтр волокнистый гальванический».** Очищает вентиляционные выбросы от аэрозолей и туманов кислот, щелочей и солей с гальванических ванн. Корпус бывает из ПП, ПВХ, ПНД, титана (ФВГ-Т) или нержавейки (ФВГ-М). Близкие обозначения: ФВА — «аэрозольный», ФКГ — «фильтр кассетный гальванический». Источники: [Plast Product](https://plast-product.ru/filtryi-voloknistyie-galvanicheskie/), [Кондор-Эко](https://kondor-eco.ru/product/82-voloknistye-filtry-tipa-fvg-t.html), [Спецвент](https://specvent.com/katalog.html). У части ПП-производителей ФВГ — собственное изделие.
6. **Порядок слов и буква «ё».** В каталогах пишут «Вставка гибкая ВГ-140*140» ([Неватом](https://www.nevatom.ru/catalog/gibkie_vstavki_vg_vo_vr_kp_vr_vr/)), а подстрока «гибкая вставка» такую строку не найдёт. Нужны варианты «вставка гибкая» и «вставки гибкие», а также приведение «ё» к «е» («крепёж/крепеж», «решётка/решетка»).
7. **Ловушка «d×S».** В каталоге ПП «Отвод 90° ПП 470×4-Фу» означает диаметр 470 и стенку 4, а «Шумоглушитель ПП 535×5-Фу» — диаметр 535 и стенку 5. Формат «Воздуховод ПП d х S х L» ([Спецвент](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/otvody.html)). ГОСТ 21.602 так же пишет «⌀76х3». Малое второе число после «х» — толщина, а не сторона прямоугольника (вывод).
8. **Буквы с несколькими значениями.** «Ф» — это диаметр (у клиентов), фланец плоский «Ф» и «Фу» (у Спецвента) и фальцевое исполнение «Ф» (РД 95 933-91). «Р» — раструб (Спецвент) или «на рамках» (РД). «ВР» — вентилятор радиальный ВР 80-75 или резиновый виброизолятор ВР 201.
9. **«Отвод» внутри тройника — это ответвление, а не отдельный отвод.** Примеры: «тройник… с отводом… угол наклона отвода» ([Полимеризделия PDF](https://izpolimera.ru/upload/katalog.pdf)), «Тройник ПП 560--400--560-Ф … отводом (второй патрубок) 400» ([Спецвент](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/trojniki.html)).
10. **«Зонт крышный» и «зонт вытяжной» — разные изделия.** Крышный ставят на выброс или шахту, его размер равен диаметру патрубка. Вытяжной — местный отсос над ванной, «форма усеченного конуса или пирамиды». Источники: [Спецвент](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/zonty-kryshnye.html), [серия 5.904-51](https://files.stroyinf.ru/Data2/2/4294852/4294852971.pdf), [УралАктив](https://uralactiv.ru/ventilyatsiya-polipropilenovaya/vozduhovody-iz-polipropilena/zonty-vytyazhnye/).
11. **Синонимы.** Отвод — «угол», «колено». Полуотвод — отвод 45°. «Штаны» — Y-тройник. «Седло», «сапожок» — врезка. «Утка» — S-образное смещение. «Прямик» — прямой участок. «Факельный выброс» ставят вместо крышного зонта. «Бортотсос» и «бортоотсос» — бортовой отсос.
12. **Единицы по ОКЕИ:** «м» (006), «пог.м» (018), «кв.м / м2» (055), «шт» (796), «компл» (839). Проектировщики часто дают воздуховоды в м² с процентной надбавкой на фасонные изделия ([форум АВОК](https://forum.abok.ru/lofiversion/index.php/t97255.html)). Метры квадратные — это не длина.
13. **Заголовки систем по ГОСТ 21.602-2016:** П, В, ПЕ, ВЕ, ДП, ДВ, ПУ, К, У, А плюс номер («П1, В1, ВЕ1, К1»). Марки элементов: ЛП и ЛВ — лючки, О — местный отсос, КП — компенсатор, КР — крепление. «№» у вентилятора — диаметр колеса в дециметрах (№ 6,3 = 630 мм).
14. **Материалы.** PP-H — гомополимер (ПП-Г). PP-B или PP-C — блок-сополимер. PP-R — рандом-сополимер. PPs — трудновоспламеняемый ПП (DIN 4102 B1). PPs-el — электропроводящий. ПНД = ПЭНД = ПЭВП = HDPE. ПЭ100 — класс по MRS, а не отдельный материал. Винипласт — непластифицированный ПВХ (ГОСТ 9639-71). ПВДФ — фторопласт-2.
15. **Граница «своё / покупное» зависит от компании.** ПП-производители сами делают каплеуловители, шумоглушители, гибкие вставки из пластика, ФВГ, скрубберы, вентиляторы ВРП, вытяжные шкафы и промышленные диффузоры. Список покупных для ameri должен утвердить руководитель (см. раздел 5).

---

## 1. Словарь синонимов: «как пишут → каноническое изделие»

### 1.1. Прямые участки

| Как пишут | Каноническое изделие | Примечание / риск путаницы | Источники |
|---|---|---|---|
| «воздуховод», «воздуховод круглый», «труба», «труба ПП», «прямой участок», «прямые вентиляционные трубы», «воздуховоды (прямые участки)» | Прямой участок круглый | Длины прямых у производителей ПП — 500, 1000, 1500, 2000, 2500, 3000 мм. У Спецвента L — «строительная длина воздуховода» | [POLEX](https://polex-vent.ru/katalog/vozduhovody-iz-polipropilena), [POLEX PDF](https://polex-vent.ru/uploads/promotional/file/2/Ventilyatsiya.pdf), [Спецвент PDF](https://specvent.com/assets/files/2025/katalog-specialnaya-ventilyaciya.pdf), [ПластПлэнт](https://plastplant.ru/plastikovye-vozduhovody/) |
| «прямик», «прямики» (кавычки есть в источниках) | Прямой участок | Жаргон производителей и монтажников. У клиента обычно с длиной и торцами: «Прямик ф250 L- 500мм - 6шт - раструб/труба» (внутр.) | [Ватер Групп](https://water-group.ru/katalog/vozduhovody/pryamougolnye-vozduhovody/), [форум АВОК](https://forum.abok.ru/lofiversion/index.php/t97255.html) (форум) |
| «короб», «короба из полипропилена», «воздуховоды (короба)», «металлические короба» | Воздуховод, чаще прямоугольный | **Высокий риск:** в прототипе «короб» считается покупной позицией (см. раздел 2) | [ПластПлэнт](https://plastplant.ru/plastikovye-vozduhovody/), [Полимеризделия](https://izpolimera.ru/vozduhovodi-polipropilen/) |
| «вентиканал», «круглые и плоские вентиканалы» | Воздуховод. «Плоский» — прямоугольный с большим отношением сторон (вывод) | — | [ПластПлэнт](https://plastplant.ru/plastikovye-vozduhovody/) |
| «Rohr», «Lüftungsrohr», «Rohr aus Plattenmaterial s=5 mm» (DE); «Pipe Piece», «round duct», «rectangular duct» (EN) | Прямой участок | «Rohr aus Plattenmaterial» — труба, сваренная из листа | [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1), [Simtech](https://www.simtechusa.com/products-and-services/air-handling/at-polypropylene-duct-systems), [XICHENG](https://air-emissions.com/pps-ducting-and-fittings) |

Термин «звено» как название прямого участка в источниках не найден (не проверено).

### 1.2. Отводы

| Как пишут | Каноническое изделие | Примечание / риск | Источники |
|---|---|---|---|
| «отвод», «отвод 90°», «отвод круглого воздуховода 90° ⌀160», «угол», «колено» | Отвод | Спецвент прямо даёт синонимы: «отвода из пластика (угла, колена)»; пример «Отвод 90° ПП 470×4-Фу» | [Спецвент — отводы](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/otvody.html) |
| «полуотвод», «Полуотвод (угол 45) ф 250» | Отвод 45° | В стальной вентиляции «полуотвод» — отвод 45°. У ПП-производителей — «отводы и полуотводы» | [Вент-Стайл](https://www.vent-style.ru/goods/ugol-45-poluotvod-f-250-iz-ocinkovannoj-stali), [POLEX](https://polex-vent.ru/katalog/vozduhovody-iz-polipropilena), [форум АВОК](https://forum.abok.ru/lofiversion/index.php/t97255.html) (форум) |
| «отвод 15/30/45/60/75/90», «отвод … с центральным углом 45°», «ОТВОД 30 / 45 / 60 / 90» | Отвод с углом | Для местных отсосов по РД — углы 15–90° «и радиусом шейки 2D» | [РД 95 933-91](https://files.stroyinf.ru/Data2/1/4293735/4293735461.pdf), [POLEX PDF](https://polex-vent.ru/uploads/promotional/file/2/Ventilyatsiya.pdf), [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1) |
| «сегментный отвод», «сектор» | Отвод, сваренный из секторов | «сегментные отводы по ВСН 353-86» — практика стальной вентиляции. Слово «сектор» как название изделия не найдено (не проверено) | [форум АВОК](https://forum.abok.ru/lofiversion/index.php/t97255.html) (форум) |
| «поворот» | Функция отвода, а не название | «Отвод — фасонная часть … для поворота оси системы на заданный угол» | [Спецвент PDF](https://specvent.com/assets/files/2025/katalog-specialnaya-ventilyaciya.pdf) |
| «Rohrbogen 15°…90° mit Muffen» (DE); «15°…90° Elbow», «elbow … centerline radius 1.0–2.0×D» (EN) | Отвод | — | [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1), [Simtech](https://www.simtechusa.com/products-and-services/air-handling/at-polypropylene-duct-systems), [XICHENG](https://air-emissions.com/pps-ducting-and-fittings) |

### 1.3. Переходы

| Как пишут | Каноническое изделие | Примечание / риск | Источники |
|---|---|---|---|
| «переход», «переход круглого сечения ⌀250-⌀200», «переход с круга на круг», «Переход ПП 560--630-Фу» | Переход круг–круг | Исполнения по расположению осей: концентрический и асимметричный. У Спецвента диаметры разделены двойным дефисом «D1--D2» | [Спецвент — переходы](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/perehody1.html), [Спецвент PDF](https://specvent.com/assets/files/2025/katalog-specialnaya-ventilyaciya.pdf), [POLEX PDF](https://polex-vent.ru/uploads/promotional/file/2/Ventilyatsiya.pdf) |
| «переход ф200/250х250», «переход с прямоугольника на круг», «переходы с круглого на прямоугольное сечение», «комбинированные переходы» | Переход круг–прямоугольник | В РД 95 933-91 это отдельный тип сечения: «тип 3 — переходное сечение (с круглого на прямоугольное)» | [SPB Active](http://spbactive.ru/production/airducts/), [POLEX PDF](https://polex-vent.ru/uploads/promotional/file/2/Ventilyatsiya.pdf), [Спецвент](https://specvent.com/katalog.html), [РД 95 933-91](https://files.stroyinf.ru/Data2/1/4293735/4293735461.pdf) |
| «переход с прямоугольника на прямоугольник», «Переход 1 400х400-500х600-800» | Переход прямоугольник–прямоугольник | На форуме формат «тип, с какого сечения, на какое, длина» (форум) | [Вентстар](https://ventstar.ru/poluotvod-45-f-560-ugol-iz-otsinkovannoj-stali/), [форум АВОК](https://forum.abok.ru/lofiversion/index.php/t97255.html) |
| «Reduzierung (mit Muffen)» (DE); «Reducer — Concentric / Eccentric» (EN) | Переход | По-русски «редукция», «переходник», «адаптер» в каталогах вентиляции не встречены (не проверено) | [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1), [Simtech](https://www.simtechusa.com/products-and-services/air-handling/at-polypropylene-duct-systems), [XICHENG](https://air-emissions.com/pps-ducting-and-fittings) |
| «конфузор», «диффузор» | **Ненадёжный синоним перехода** | «Входной конфузор» — деталь вентилятора. «Диффузор» — деталь дефлектора («1 — Диффузор») или воздухораспределитель («Промышленные диффузоры» из пластика, «Круглый потолочный диффузор»). См. раздел 2 | [Неватом — вентиляторы](https://www.nevatom.ru/catalog/radialnye_ventilyatory/filter/design-is-vzryvozashchishchennoe_korrozionnostoykoe_teplostoykoe/apply/), [серия 5.904-51](https://files.stroyinf.ru/Data2/2/4294852/4294852971.pdf), [Plast Product — диффузоры](https://plast-product.ru/promyshlennye-diffuzory-plastikovye) |

### 1.4. Утка (смещение)

| Как пишут | Каноническое изделие | Примечание / риск | Источники |
|---|---|---|---|
| «утка», «утка вентиляционная из полипропилена», «утки … круглые и прямоугольные» | Утка — S-образный элемент со смещением оси | «S-образное фасонное изделие для огибания препятствий — … трасса воздуховодов смещается вертикально или горизонтально». По Неватому: «У вентиляционных уток отсутствует заужение сечения. Если необходимо заужение, следует заказывать … переходы» | [SPB Active — утка](http://spbactive.ru/production/airducts/utka/), [Неватом — утки](https://www.nevatom.ru/catalog/utki/) |

Слова «обвод» и «смещение» как названия изделия в найденных каталогах не встречены (не проверено).

### 1.5. Тройники, врезки, крестовины

| Как пишут | Каноническое изделие | Примечание / риск | Источники |
|---|---|---|---|
| «тройник», «Тройник ПП 560-Фу», «тройник ф110» без второго размера, «равнопроходной», «Т-образный» | Тройник равнопроходной | Спецвент: «с диаметром всех трёх патрубков 560 мм». В ameri уже есть правило: без второго размера branch_d = d (внутр.) | [Спецвент — тройники](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/trojniki.html) |
| «тройник переходной», «Тройник ПП 560--400--560-Ф», «Тройник ⌀250-⌀160», «ф250/ф160/ф250» | Тройник переходной | Порядок у Спецвента: магистраль – ответвление – магистраль. У клиентов бывает «магистраль-ответвление» (внутр.) | [Спецвент — тройники](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/trojniki.html) |
| «тройник под углом 45 гр.», «косой тройник», «T-Stück 45°», «45° Lateral» | Тройник с косым ответвлением | Тройники бывают «прямые и косые с любым углом поворота врезки относительно оси основной» магистрали | [Спецвент PDF](https://specvent.com/assets/files/2025/katalog-specialnaya-ventilyaciya.pdf), [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1), [Simtech](https://www.simtechusa.com/products-and-services/air-handling/at-polypropylene-duct-systems) |
| «штаны», «тройник Y (штаны) D160-D160-D160», «тройник штанообразный», «Hosen T-Stück», «Wye 30°/45°/90°» | Y-тройник («штаны») | — | [ВентКом](https://ventkom.com/fasonnye-izdeliya-dlya-spiralno-navivnyh-vozduhovodov/trojnik-y-shtany/), [РД 95 933-91](https://files.stroyinf.ru/Data2/1/4293735/4293735461.pdf), [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1), [Simtech](https://www.simtechusa.com/products-and-services/air-handling/at-polypropylene-duct-systems) |
| «врезка круглого сечения», «врезка прямоугольного сечения», «Врезка седло прямоугольный воздуховод 900/300*500», «седло», «врезки с „сапожками“», «Sattelstutzen 90°/45° Abgang», «90° Saddle» | Врезка — патрубок ответвления, вваренный в стенку магистрали | Это отдельное изделие, не тройник. Как его считать, решает руководитель (вывод) | [SPB Active](http://spbactive.ru/production/airducts/), [ТехноВент](https://vektorvent.ru/articles/flancevoe-soedinenie-vozduhovodov/), [форум АВОК](https://forum.abok.ru/lofiversion/index.php/t97255.html) (форум), [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1), [Simtech](https://www.simtechusa.com/products-and-services/air-handling/at-polypropylene-duct-systems) |
| «крестовина», «крестовины и заглушки» | Крестовина (четыре патрубка) | — | [SPB Active](http://spbactive.ru/production/airducts/), [POLEX PDF](https://polex-vent.ru/uploads/promotional/file/2/Ventilyatsiya.pdf), [Неватом — тройники](https://www.nevatom.ru/catalog/troyniki/) |
| «… с отводом», «угол наклона отвода» внутри описания тройника | Патрубок ответвления тройника | **Не отдельный отвод** | [Полимеризделия PDF](https://izpolimera.ru/upload/katalog.pdf), [Спецвент — тройники](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/trojniki.html) |

### 1.6. Заглушки

| Как пишут | Каноническое изделие | Примечание / риск | Источники |
|---|---|---|---|
| «заглушка», «заглушка вентиляционная», «Заглушка воздуховода (прямоугольная)», «ЗАГЛУШКА» | Заглушка | В ameri от неё считается цена решётки: 2 × цена заглушки того же сечения (внутр.) | [POLEX PDF](https://polex-vent.ru/uploads/promotional/file/2/Ventilyatsiya.pdf), [SPB Active](http://spbactive.ru/production/airducts/), [Вентстар](https://ventstar.ru/poluotvod-45-f-560-ugol-iz-otsinkovannoj-stali/) |
| «End Cap» (EN), «Endboden mit Muffe» (DE, дословно «донышко с муфтой»), «Blindflansch» / «Blind Flange» — глухой фланец | Заглушка торцевая или фланцевая | «Торцевая крышка», «пробка» и «донышко» как русские названия в каталогах вентиляции не найдены (не проверено) | [Simtech](https://www.simtechusa.com/products-and-services/air-handling/at-polypropylene-duct-systems), [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1), [FRANK](https://www.frank-gmbh.de/de-wAssets/docs/download-deutsch/download/preislisten/aktuelle_preislisten/17-Preisliste-flansche-sonderteile-komplett.pdf) |

### 1.7. Соединители и виды соединений

| Как пишут | Каноническое | Примечание / риск | Источники |
|---|---|---|---|
| «ниппель», «Ниппель ⌀250», «ниппельное соединение» | Ниппель — внутренний соединитель | В стальной вентиляции: «Ниппель для соединения прямых участков воздуховодов между собой. Муфта для соединения фасонных изделий между собой». У ПП: «длину воздуховода легко … нарастить (при помощи муфты или ниппеля)». У Тетры «ниппель» — вид соединения: «фланец; раструб (ниппель)» | [Технократ](https://tehnokrat-omsk.ru/nipel.html), [Полиюнион](https://polyunion.ru/ventilyatsionnye-sistemy/vozduhovody-ventiljacija-iz-polipropilena), [Тетра](https://prom-emkosti.ru/produktsiya/himstojkie-vozduhovody/vozduhovody-iz-polipropilena/) |
| «муфта», «муфтовое соединение», «М», «Doppelmuffe», «Coupling» | Муфта — наружный соединитель, или вид соединения по торцу | Коды Спецвента: «фланец Ф, фланец под уплотнение Фу, раструб Р, муфта М». У Полиюниона «раструбное (муфтовое)» — одно и то же | [Спецвент PDF](https://specvent.com/assets/files/2025/katalog-specialnaya-ventilyaciya.pdf), [Полиюнион](https://polyunion.ru/ventilyatsionnye-sistemy/vozduhovody-ventiljacija-iz-polipropilena), [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1), [Simtech](https://www.simtechusa.com/products-and-services/air-handling/at-polypropylene-duct-systems) |
| «бандаж», «бандажное соединение (Б)», «Бандаж 200 РД 95 933» | Бандаж — соединение стальных воздуховодов | Для ПП не встречен (вывод) | [РД 95 933-91](https://files.stroyinf.ru/Data2/1/4293735/4293735461.pdf) |
| «раструб», «раструбное соединение», «Р», «раструб/труба» (внутр.), «socket (push-fit) … back-welding» | Раструбный конец или раструбное соединение | У Спецвента раструб на круглых — «до d355 мм включительно». Герметичность — «проваривается … присадочным прутком». Торцевые соединения — открытый вопрос Q41 | [Спецвент](https://specvent.com/katalog.html), [Полиюнион](https://polyunion.ru/ventilyatsionnye-sistemy/vozduhovody-ventiljacija-iz-polipropilena), [XICHENG](https://air-emissions.com/pps-ducting-and-fittings) |
| «фланец», «плоский фланец Ф», «фланец под уплотнение Фу», «Фланец плоский прижимной», «Фланец шириной 45 мм с отверстиями под болтовое соединение», «фланец20» (внутр.) | Фланец или фланцевое соединение | Бывают отдельной позицией («Фланец плоский прижимной» у SPB Active). В каталогах есть и ширина фланца (45 мм), и толщина (Ф/Фу 10–15 мм), так что «фланец20» неоднозначен. Это открытый вопрос Q40 | [Спецвент](https://specvent.com/katalog.html), [Спецвент — зонты](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/zonty-kryshnye.html), [SPB Active](http://spbactive.ru/production/airducts/), [Полиюнион](https://polyunion.ru/ventilyatsionnye-sistemy/vozduhovody-ventiljacija-iz-polipropilena) |
| «бурт», «втулка под фланец (бурт)», «накидной / свободный фланец», «Vorschweißbund», «Bundbuchse», «Losflansch / Backing ring», «loose-ring (backup ring) flange» | Бурт — приварной воротник плюс свободный фланец | Это термины трубопроводов ПЭ и ПП-Р. В ПП-вентиляции встречаются редко (вывод). Слова «бортовое кольцо» и «отбортовка» как синонимы бурта не найдены (не проверено) | [GREMIR](https://gremir.ru/flantsy/flantsy-pod-burt-pod-pe-vtulku/), [Valfex](https://valfex.ru/catalog/polipropilenovye-fitingi-seriya-standard/burt-polipropilenovyy-pod-flanets/), [FRANK](https://www.frank-gmbh.de/de-wAssets/docs/download-deutsch/download/preislisten/aktuelle_preislisten/17-Preisliste-flansche-sonderteile-komplett.pdf), [XICHENG](https://air-emissions.com/pps-ducting-and-fittings) |
| «сварка встык», «стыковая сварка на станке», «экструзионная / полифузионная сварка», «Stumpfschweißung» | Сварное соединение | — | [Полимеризделия](https://izpolimera.ru/vozduhovodi-polipropilen/), [Полиюнион](https://polyunion.ru/ventilyatsionnye-sistemy/vozduhovody-ventiljacija-iz-polipropilena), [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1) |

### 1.8. Регулирующие и запорные элементы

| Как пишут | Каноническое изделие | Своё или покупное / риск | Источники |
|---|---|---|---|
| «шибер», «шиберная заслонка», «шиберная задвижка», «заслонка», «Шибер (заслонка)», «Заслонка шиберная ПП d …», «blast gate (guillotine damper)» | Шибер | Из ПП — **своё**. Определение: «элемент вентиляции с выдвижной пластиной, предназначенный для полного перекрытия вентиляционного канала» | [Спецвент PDF](https://specvent.com/assets/files/2025/katalog-specialnaya-ventilyaciya.pdf), [Спецвент](https://specvent.com/katalog.html), [Полимеризделия](https://izpolimera.ru/vozduhovodi-polipropilen/), [ПластПлэнт](https://plastplant.ru/plastikovye-vozduhovody/), [XICHENG](https://air-emissions.com/pps-ducting-and-fittings) |
| «дроссель-клапан», «клапаны дроссельные», «Дроссель-клапан ПП 560-Фу», «Drosselklappe mit Handhebel», «butterfly damper», «Damper w/ Locking Handle» | Дроссель-клапан | Из ПП — **своё**. Определение: «фасонная часть … с поворотным запорным элементом». «Drosselklappen dienen zum Regulieren des Volumenstromes» | [Спецвент — ДК](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/shibernye-zaslonki1.html), [SPB Active](http://spbactive.ru/production/airducts/), [SR](https://www.sr-kunststofftechnik.de/drosselklappen.html), [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1), [Simtech](https://www.simtechusa.com/products-and-services/air-handling/at-polypropylene-duct-systems) |
| «дроссель-клапан с электроприводом», «Дроссель-клапан ПП-ЭП 560-Ф», «с площадкой под электропривод», «Regelklappe mit Flansch für Stellantrieb» | ПП-дроссель-клапан с покупным приводом | **Смешанная позиция:** корпус свой, привод покупной. Привод бывает «manuell, elektrisch oder pneumatisch» | [Спецвент — ДК-ЭП](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/drossel-klapany-s-elektroprivodom.html), [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1), [SR](https://www.sr-kunststofftechnik.de/drosselklappen.html) |
| «КВР», «клапан воздушный регулирующий» | Стальной многостворчатый клапан — **покупной** | Для сред, «агрессивность которых по отношению к углеродистым сталям … не выше агрессивности воздуха». Состоит из «корпуса, поворотных лопаток, привода». С ПП-дроссель-клапаном не путать | [МаксАэро](https://www.maxaero.by/katalog-produkcii/sobstvennoe-proizvodstvo/zaslonki-vozdushnye/klapan-vozdushnyy-reguliruyushchiy-tipa-kvr) |
| «клапан ирисовый», «ирисовый клапан», «IRIS», «SPI» | Ирисовый клапан-регулятор — **покупной** (сталь) | «предназначены для регулирования потока воздуха и измерения его расхода в воздушных каналах круглого сечения» | [РОВЕН](https://rowen.ru/catalog/ventilyatsionnye_klapany/klapany_irisovye/) |
| «регулятор расхода», «Volume Flow Controller» | Регулятор расхода (VAV) | У Simtech есть из ПП. Своё это или покупное, уточнить у руководителя | [Simtech](https://www.simtechusa.com/products-and-services/air-handling/at-polypropylene-duct-systems) |
| «обратный клапан», «Обратный клапан ПП 560-Фу», «Rückschlagklappe für senkrechter Einbau», «Back Draft Damper», «backdraft damper … gravity-closing PP flap» | Обратный клапан | Из ПП — **своё**. Стальные «Клапан обратный КО Ф100 („бабочка“)» — покупные: «закрывается за счет давления пружин», «корпус … из оцинкованной стали, лопатки из алюминия». Русское «гравитационный» встречено только в выдаче поиска (не проверено) | [Спецвент — обратные](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/obratnye-klapany.html), [Полимеризделия](https://izpolimera.ru/vozduhovodi-polipropilen/), [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1), [Simtech](https://www.simtechusa.com/products-and-services/air-handling/at-polypropylene-duct-systems), [XICHENG](https://air-emissions.com/pps-ducting-and-fittings), [Неватом — КО](https://www.nevatom.ru/catalog/klapany_obratnye_ko_babochka/) |
| «перекидной клапан», «клапан перекидной», «Перекидной клапан ПП 560×560-Фу» | Перекидной (переключающий) клапан | Из ПП — **своё** | [Спецвент — перекидные](https://specvent.com/katalog/ventilyaciya-pryamougolnogo-secheniya/perekidnye-klapany.html), [SPB Active](http://spbactive.ru/production/airducts/) |

### 1.9. Выброс: зонт крышный, дефлектор, факельный выброс

| Как пишут | Каноническое изделие | Примечание / риск | Источники |
|---|---|---|---|
| «зонт», «зонт крышный», «Зонт круглый 250» (внутр.), «Зонт крышный ПНД 560-Фу», «ЗК.00.000», «зонты вентиляционные», «Regenhaube» | **Зонт крышный** — на выбросе или шахте | «Зонты устанавливаются на вытяжных вентиляционных шахтах … с целью защиты шахт от попадания в них атмосферных осадков. Типоразмер зонта принимается соответственно наружному размеру горловины шахты». У Спецвента D — «наружный диаметр» из ряда диаметров воздуховодов 110…2100 | [серия 5.904-51](https://files.stroyinf.ru/Data2/2/4294852/4294852971.pdf), [Спецвент — зонты](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/zonty-kryshnye.html), [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1) |
| «колпак» | Деталь зонта; «дефлекторный колпак» — дефлектор | У зонта ЗК: «1 — Колпак, 2 — Лапка, 3 — Пояс, 4 — Фланец» | [серия 5.904-51](https://files.stroyinf.ru/Data2/2/4294852/4294852971.pdf), [SPB Active](http://spbactive.ru/production/airducts/), [Полимеризделия](https://izpolimera.ru/vozduhovodi-polipropilen/) |
| «дефлектор», «дефлекторный колпак», «Д 315.00.000», «Deflektorhaube», «Deflector — Socket / Flanged» | Дефлектор | «Дефлекторы устанавливаются на вытяжных шахтах в системах естественной вентиляции… Дефлекторы имеют номера от 3 до 10 соответственно наружному диаметру шахты, выраженному в дециметрах». Детали: «Диффузор, Цилиндр, Зонт, Лапка, Конус, Фланец». Deflektorhaube — «Abschluss einer vertikalen Ausblasleitung». Название «дефлектор ЦАГИ» в загруженных источниках не найдено (не проверено). Серия 1.494-32 «Зонты и дефлекторы вентиляционных систем» по данным поиска заменена серией 5.904-51 (не проверено) | [серия 5.904-51](https://files.stroyinf.ru/Data2/2/4294852/4294852971.pdf), [SR](https://www.sr-kunststofftechnik.de/deflektorhaube.html), [Simtech](https://www.simtechusa.com/products-and-services/air-handling/at-polypropylene-duct-systems), [серия 1.494-32](https://standartgost.ru/g/%D0%A1%D0%B5%D1%80%D0%B8%D1%8F_1.494-32) |
| «факельный выброс», «Exhaust Stack (w/ Bypass)» | Факельный выброс — вертикальный выброс вместо зонта | Отдельное изделие в перечне ПП-производителя | [POLEX](https://polex-vent.ru/katalog/vozduhovody-iz-polipropilena), [Simtech](https://www.simtechusa.com/products-and-services/air-handling/at-polypropylene-duct-systems) |
| «узел прохода через кровлю», «Dachaufsatz», «Wanddurchführung» | Узел прохода через кровлю или стену | Из ПП — своё у производителей | [Спецвент](https://specvent.com/katalog.html), [SPB Active](http://spbactive.ru/production/airducts/), [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1) |

### 1.10. Местные отсосы: зонт вытяжной, бортовой отсос

| Как пишут | Каноническое изделие | Примечание / риск | Источники |
|---|---|---|---|
| «зонт вытяжной», «вытяжной зонт», «зонты-козырьки», «зонт подвесной», «зонт для установки на борт ванны», «вытяжные панели», «местный отсос» | **Местный отсос** — зонт над ванной или оборудованием | **Не путать с крышным зонтом.** «Вытяжные зонты и зонты-козырьки относятся к местным отсосам открытого типа… над колокольными ваннами… форму усеченного конуса или пирамиды». Спецвент делает их по чертежам заказчика. Марка элемента по ГОСТ 21.602 — «О» (местный отсос) | [УралАктив](https://uralactiv.ru/ventilyatsiya-polipropilenovaya/vozduhovody-iz-polipropilena/zonty-vytyazhnye/), [Спецвент](https://specvent.com/katalog.html), [SPB Active](http://spbactive.ru/production/airducts/), [Plast Product](https://plast-product.ru/shkaf-zont-rechetki), [ГОСТ 21.602-2016](https://www.eng-in.ru/images/spravka/normativ/GOST-21.602-2016.pdf) |
| «бортовой отсос», «бортотсос», «бортоотсос», «борт отсос», «Бортовой отсос ПП БО вид 2 - Фу», «односторонний / двусторонний», «опрокинутый» | Бортовой отсос (щелевой, на борт ванны) | Из ПП — своё. Комплектуется «люками ревизии» и «встроенными дроссельными клапанами» | [Спецвент — бортотсосы](https://specvent.com/bortovye-otsosy-iz-polipropilena-i-polietilena-dlya-galvanicheskih-vann.html), [УралАктив](https://uralactiv.ru/ventilyatsiya-polipropilenovaya/elementy-ventilyatsii/bortovye-otsosy/), [Полимеризделия PDF](https://izpolimera.ru/upload/katalog.pdf), [Plast Product](https://plast-product.ru/shkaf-zont-rechetki) |

### 1.11. Решётки и сетки

| Как пишут | Каноническое изделие | Примечание / риск | Источники |
|---|---|---|---|
| «решётка», «решетка вентиляционная», «решётки круглые / прямоугольные», «решетка жалюзийная», «Решетка жалюзийная ПП 560-Ф», «Zu- und Abluftgitter» | Решётка (из ПП) | В ameri цена решётки = 2 × заглушка того же сечения (внутр.) | [Спецвент — решётки](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/reshetki-kruglye.html), [SPB Active](http://spbactive.ru/production/airducts/), [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1) |
| «защитная сетка», «сетка», «Vogelschutzgitter», «Bird Mesh Grille w/ SS Screen» | Защитная сетка; в ameri её считают решёткой (внутр.) | Сетка бывает из нержавейки (у Simtech — «SS Screen») | [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1), [SR](https://www.sr-kunststofftechnik.de/deflektorhaube.html), [Simtech](https://www.simtechusa.com/products-and-services/air-handling/at-polypropylene-duct-systems) |

### 1.12. Гибкие вставки и компенсаторы

| Как пишут | Каноническое изделие | Примечание / риск | Источники |
|---|---|---|---|
| «гибкая вставка», «Вставка гибкая ВГ-140*140-…», «Гибкие вставки (компенсаторы) антивибрационные», «гибкая вставка (вибровставка)», «ВГК / ВГС / ВГП», «вставка гибкая типа „В“ / „Н“ (по серии 5.904-38)» | Гибкая (виброизолирующая) вставка — **покупная** у компании | **Порядок слов «вставка гибкая»** — подстрока «гибкая вставка» его не найдёт. Тип «В» ставят на всасывании (круглая), «Н» — на нагнетании (прямоугольная) | [Неватом — вставки](https://www.nevatom.ru/catalog/gibkie_vstavki_vg_vo_vr_kp_vr_vr/), [Аэрдин](https://aerdyn.ru/gibkie-vstavki/), [СибВентКомплекс](http://www.sibvent.kz/node/49), [Градвент](https://gradvent.com/komplektuyushchie/gibkaya-vstavka) |
| «Хим. стойкие гибкие вставки из пластика», «гибкие вставки для вентиляторов», «Wellmanschette (Manschette aus Weich-PVC und Spannband)», «Expansion Joint — Socket / Clip Band / Flanged 4-/6-Fold» | То же, но из пластика | У ПП-производителей это собственная продукция. Для ameri по заданию — покупная | [Спецвент](https://specvent.com/katalog.html), [SPB Active](http://spbactive.ru/production/airducts/), [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1), [Simtech](https://www.simtechusa.com/products-and-services/air-handling/at-polypropylene-duct-systems) |
| «компенсатор длины» | Компенсатор температурных удлинений (ПП) | **Омоним:** Неватом называет гибкие вставки «компенсаторами» | [SPB Active](http://spbactive.ru/production/airducts/), [Неватом — вставки](https://www.nevatom.ru/catalog/gibkie_vstavki_vg_vo_vr_kp_vr_vr/) |

«Мягкая вставка» и «гибкий патрубок» как названия в найденных каталогах не встречены (не проверено).

### 1.13. Ревизия и лючки

| Как пишут | Каноническое изделие | Примечание / риск | Источники |
|---|---|---|---|
| «люк ревизии», «лючок для чистки воздуховодов» (ЛВ), «лючок для замеров параметров воздуха» (ЛП), «Reinigungsöffnung», «Clean-Out», «Clean-Out Tee» | Ревизионный люк или лючок | «ЛВ1», «ЛП1» — марки элементов по ГОСТ 21.602, их можно встретить в спецификации как позицию | [ГОСТ 21.602-2016](https://www.eng-in.ru/images/spravka/normativ/GOST-21.602-2016.pdf), [Спецвент — бортотсосы](https://specvent.com/bortovye-otsosy-iz-polipropilena-i-polietilena-dlya-galvanicheskih-vann.html), [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1), [Simtech](https://www.simtechusa.com/products-and-services/air-handling/at-polypropylene-duct-systems) |

### 1.14. Прочие изделия, которые делают из ПП

| Как пишут | Каноническое изделие | Примечание / риск | Источники |
|---|---|---|---|
| «каплеуловитель», «каплеуловитель из полипропилена», «каплеотбойные кассеты из полипропилена» | Каплеуловитель (сепаратор капель) | У ПП-производителей — своё изделие: «Для производства каплеуловителя используется полипропилен…». Ставится и в ФВГ | [SPB Active](http://spbactive.ru/production/airducts/), [ПластПП](https://msk.plastpp.ru/cleaning-system/drop-traps/), [НПО Нева-Актив](https://npo-neva-aktiv.ru/kapleuloviteli/), [Спецвент](https://specvent.com/katalog.html) |
| «шумоглушитель», «глушители шума», «Шумоглушитель ПП 535×5-Фу», «Rohrschalldämpfer … Kulissenlänge 500 mm», «Muffler 1250 mm long» | Шумоглушитель | Из ПП — у производителей. Стальные ГТК и ГТП — покупные (раздел 4) | [Спецвент — глушители](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/shumoglushiteli.html), [Полимеризделия](https://izpolimera.ru/vozduhovodi-polipropilen/), [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1), [Simtech](https://www.simtechusa.com/products-and-services/air-handling/at-polypropylene-duct-systems) |

### 1.15. Материалы и их обозначения

| Как пишут | Каноническое | Примечание / риск | Источники |
|---|---|---|---|
| «ПП», «PP», «ПП/РР», «полипропилен» | Полипропилен | «По умолчанию полипропилен серого цвета, ПНД — черного». У Спецвента «полипропилена ПП/РР» набрано **кириллическими** «РР» (проверено по кодам символов U+0420). Сравнивать надо и «pp», и «рр» | [SPB Active](http://spbactive.ru/production/airducts/), [Спецвент](https://specvent.com/katalog.html) |
| «PP-H», «ПП-Г», «ПП тип 1», «гомополимер», «PP-H AlphaPlus» | Гомополимер ПП | У Спецвента PP-H — «только прямоугольного сечения» | [Valtec](https://valtec.ru/document/article/know_about_polypropilen.html), [SIMONA tech.info](https://www.simona.de/fileadmin/user_upload/Medien/Mediacenter/Technische_Informationen/tech.info_SIMONA_PP_-deutsch-.pdf), [Спецвент PDF](https://specvent.com/assets/files/2025/katalog-specialnaya-ventilyaciya.pdf) |
| «PP-B», «ПП-Б», «ПП тип 2», «блоксополимер», «PP-C», «ПП-сополимер» | Блок-сополимер ПП | У SIMONA «PP-C (Block-Copolymer)». Спецвент: «наиболее распространенный при изготовления воздуховодов ПП-сополимер» (орфография источника). Полиюнион: «листового полипропилена (блоксополимера)» | [Valtec](https://valtec.ru/document/article/know_about_polypropilen.html), [SIMONA](https://www.simona.de/fileadmin/user_upload/Medien/Mediacenter/Technische_Informationen/tech.info_SIMONA_PP_-deutsch-.pdf), [Спецвент](https://specvent.com/katalog.html), [Полиюнион](https://polyunion.ru/ventilyatsionnye-sistemy/vozduhovody-ventiljacija-iz-polipropilena) |
| «PP-R», «ПП-Р», «ПП тип 3», «рандом сополимер» | Рандом-сополимер ПП | Материал сантехнических труб. В каталогах вентиляции не встречен (вывод) | [Valtec](https://valtec.ru/document/article/know_about_polypropilen.html), [SIMONA](https://www.simona.de/fileadmin/user_upload/Medien/Mediacenter/Technische_Informationen/tech.info_SIMONA_PP_-deutsch-.pdf) |
| «PPs», «Polypropylen schwerentflammbar», «PPs негорючий полипропилен», «трудногорючий ПП» | Трудновоспламеняемый ПП | SIMONA: PPs «nach DIN 4102 Teil 1 als schwerentflammbarer Baustoff Klasse B1», а обычный PP — B2. У XICHENG PPs — UL 94 V-0, «dark grey / black». Слово «негорючий» у Plast Product — маркетинг, по DIN это B1 (вывод) | [SIMONA](https://www.simona.de/fileadmin/user_upload/Medien/Mediacenter/Technische_Informationen/tech.info_SIMONA_PP_-deutsch-.pdf), [SR](https://www.sr-kunststofftechnik.de/drosselklappen.html), [Plast Product](https://plast-product.ru/shkaf-zont-rechetki), [XICHENG](https://air-emissions.com/pps-ducting-and-fittings) |
| «PPs-el», «PP-EL», «PP-El-s», «PPs EL антистатичный», «электропроводящий ПП» | Электропроводящий (антистатический) ПП | Для взрывоопасных зон: «электропроводящего ПП марки PP-EL» | [SR](https://www.sr-kunststofftechnik.de/drosselklappen.html), [SIMONA](https://www.simona.de/fileadmin/user_upload/Medien/Mediacenter/Technische_Informationen/tech.info_SIMONA_PP_-deutsch-.pdf), [Спецвент PDF](https://specvent.com/assets/files/2025/katalog-specialnaya-ventilyaciya.pdf), [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1) |
| «ПП-УФ», «полипропилен с УФ-стабилизацией» | УФ-стабилизированный ПП | Для наружной установки | [Спецвент — зонты](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/zonty-kryshnye.html) |
| «ПНД», «ПЭНД», «ПЭВП», «HDPE», «PE-HD», «ПЭ», «PE», «ПНД/ПЭ» | Полиэтилен низкого давления (высокой плотности) | «Полиэтиленом высокой плотности низкого давления (ПНД или ПЭНД)». Чёрный ПНД — с сажей, стойкий к УФ. Не путать с ПВД / ПЭВД (вывод) | [Энгпласт](https://www.engplast.ru/materialy/polietileny-pe/polietilen-nizkogo-davleniya-pend-hdpe/), [Спецвент](https://specvent.com/katalog.html) |
| «ПЭ100», «PE100», «ПЭ80», «ПЭ63» | Марка ПЭ по MRS, а не отдельный материал | «обозначения ПЭ63, ПЭ80, ПЭ100 … в основе имеют показатель MRS» | [Энгпласт](https://www.engplast.ru/materialy/polietileny-pe/polietilen-nizkogo-davleniya-pend-hdpe/) |
| «ПВХ», «PVC», «PVC U», «винипласт», «непластифицированный ПВХ» | Жёсткий (непластифицированный) ПВХ | ГОСТ 9639-71 — «Листы из непластифицированного поливинилхлорида (винипласт листовой)». У Спецвента ПВХ — «только прямоугольного сечения», внутри помещений, «высокая хрупкость». Сочетания «ПВХ-НП» и «PVC-U» с дефисом в источниках не встречены (не проверено) | [ГОСТ 9639-71 (plastinfo)](https://plastinfo.ru/information/standart/20/445/), [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1), [Спецвент PDF](https://specvent.com/assets/files/2025/katalog-specialnaya-ventilyaciya.pdf) |
| «PVDF», «ПВДФ», «фторопласт-2», «Ф-2М» | Поливинилиденфторид | «Техническое название — фторопласт-2». У Plast Product: «PVDF (ПВДФ – фторопласт-2)». Тетра делает воздуховоды из ПВДФ | [Википедия](https://ru.wikipedia.org/wiki/%D0%9F%D0%BE%D0%BB%D0%B8%D0%B2%D0%B8%D0%BD%D0%B8%D0%BB%D0%B8%D0%B4%D0%B5%D0%BD%D1%84%D1%82%D0%BE%D1%80%D0%B8%D0%B4), [Plast Product](https://plast-product.ru/shkaf-zont-rechetki), [Тетра](https://prom-emkosti.ru/produktsiya/himstojkie-vozduhovody/vozduhovody-iz-polipropilena/) |

---

## 2. Опасные омонимы: одно слово — разные изделия

| Слово | Значения | Как различить (вывод) | Источники | Рекомендация |
|---|---|---|---|---|
| **зонт** | (1) зонт крышный на выбросе, размер — патрубок; (2) зонт вытяжной — местный отсос над ванной, форма пирамиды или конуса; (3) деталь дефлектора («3 — Зонт») | «крышный», «круглый ⌀», «на выброс» → (1). «вытяжной», «над ванной», «козырёк», «подвесной», размер АхВ крупный → (2) | [серия 5.904-51](https://files.stroyinf.ru/Data2/2/4294852/4294852971.pdf), [УралАктив](https://uralactiv.ru/ventilyatsiya-polipropilenovaya/vozduhovody-iz-polipropilena/zonty-vytyazhnye/), [SPB Active](http://spbactive.ru/production/airducts/) | Без признаков задавать вопрос. Не мапить «зонт вытяжной» в umbrella_round |
| **короб** | (1) воздуховод, обычно прямоугольный; (2) вне вентиляции — кабельный короб (вывод) | Есть размеры АхВ, «ПП», длина или «м» → (1) | [ПластПлэнт](https://plastplant.ru/plastikovye-vozduhovody/), [Полимеризделия](https://izpolimera.ru/vozduhovodi-polipropilen/) | **Убрать «короб» из покупных** или сузить до «кабельный короб», «кабель-канал» |
| **клапан** | Дроссель-клапан ПП, обратный ПП, перекидной ПП — своё; КВР, КПУ, КЛОП, ирисовый — покупное | Своё: марка из ПП или слова «дроссель», «обратный», «перекидной». Покупное: марка КВР, КПУ, КЛОП, SPI или Belimo | [Спецвент](https://specvent.com/katalog.html), [МаксАэро](https://www.maxaero.by/katalog-produkcii/sobstvennoe-proizvodstvo/zaslonki-vozdushnye/klapan-vozdushnyy-reguliruyushchiy-tipa-kvr), [МашПром](https://www.mashprom.org/ventilyacyonnoe_oborudovanie/klapan_protivopozharnyj_kpu_1_kpu_2_kpu_3/) | Не добавлять «клапан» в покупные |
| **муфта** | (1) соединитель; (2) вид соединения «М»; (3) у ряда производителей — то же, что раструб («раструбное (муфтовое)») | По контексту: отдельная позиция с количеством → (1); в хвосте строки → вид соединения | [Спецвент PDF](https://specvent.com/assets/files/2025/katalog-specialnaya-ventilyaciya.pdf), [Полиюнион](https://polyunion.ru/ventilyatsionnye-sistemy/vozduhovody-ventiljacija-iz-polipropilena), [Технократ](https://tehnokrat-omsk.ru/nipel.html) | — |
| **ниппель** | (1) изделие-соединитель; (2) у Тетры вид соединения «раструб (ниппель)» | Как у «муфты» | [Тетра](https://prom-emkosti.ru/produktsiya/himstojkie-vozduhovody/vozduhovody-iz-polipropilena/), [Полиюнион](https://polyunion.ru/ventilyatsionnye-sistemy/vozduhovody-ventiljacija-iz-polipropilena) | — |
| **хомут** | (1) стальной хомут с резинкой для крепления круглого воздуховода; (2) крепёж на монтаже («хомут+струбцина+шпилька») | Оба значения — покупные | [форум АВОК](https://forum.abok.ru/lofiversion/index.php/t97255.html) (форум), «Хомут ф250 с резинкой» (внутр.) | Оставить в покупных |
| **фланец** | (1) часть изделия, вид соединения Ф/Фу; (2) отдельный ПП-фланец («Фланец плоский прижимной»); (3) стальной свободный или накидной фланец под бурт; (4) «фланец20» — неизвестно, ширина это или толщина (Q40) | Ф/Фу/Р/М в конце обозначения → вид соединения | [Спецвент](https://specvent.com/katalog.html), [SPB Active](http://spbactive.ru/production/airducts/), [GREMIR](https://gremir.ru/flantsy/flantsy-pod-burt-pod-pe-vtulku/) | Q40 не решать догадкой |
| **отвод** | (1) отвод (колено); (2) ответвление тройника («тройник … с отводом») | Слово «тройник» в той же строке → (2) | [Полимеризделия PDF](https://izpolimera.ru/upload/katalog.pdf), [Спецвент — тройники](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/trojniki.html) | Правило разбора: внутри тройника «отвод» — branch |
| **диффузор / конфузор** | (1) расширяющийся или сужающийся переход (не проверено); (2) деталь дефлектора; (3) воздухораспределитель («Круглый потолочный диффузор», «Промышленные диффузоры» из пластика); (4) «входной конфузор» вентилятора | — | [серия 5.904-51](https://files.stroyinf.ru/Data2/2/4294852/4294852971.pdf), [Plast Product](https://plast-product.ru/promyshlennye-diffuzory-plastikovye), [Неватом](https://www.nevatom.ru/catalog/radialnye_ventilyatory/filter/design-is-vzryvozashchishchennoe_korrozionnostoykoe_teplostoykoe/apply/) | Не добавлять ни в покупные, ни в синонимы перехода; задавать вопрос |
| **компенсатор** | (1) гибкая вставка — «Гибкие вставки (компенсаторы)»; (2) «Компенсатор длины» из ПП; (3) марка «КП» по ГОСТ 21.602 | «длины» или «температурный» → (2) | [Неватом](https://www.nevatom.ru/catalog/gibkie_vstavki_vg_vo_vr_kp_vr_vr/), [SPB Active](http://spbactive.ru/production/airducts/), [ГОСТ 21.602](https://www.eng-in.ru/images/spravka/normativ/GOST-21.602-2016.pdf) | Не добавлять «компенсатор» в покупные |
| **шумоглушитель** | (1) из ПП — своё у производителей; (2) стальные ГТК, ГТП, ГП по серии 5.904-17 — покупные | Марка ГТК/ГТП или «оцинк» → (2) | [Спецвент](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/shumoglushiteli.html), [Интеркон](http://intercon.com.ua/wp-content/uploads/2019/06/GTK-GTP-GP-min.pdf) | Спросить руководителя, делает ли компания ПП-глушители |
| **фильтр** | ФВГ, ФВА, ФКГ — у ПП-производителей своё (ФВГ-ПП), для ameri покупное; «фильтр ФЛП» — стальной покупной | — | [Plast Product](https://plast-product.ru/filtryi-voloknistyie-galvanicheskie/), [УралАктив](https://uralactiv.ru/gazoochistnoe-oborudovanie/voloknistye-filtry-fvg/), [Вент-Стайл](https://www.vent-style.ru/goods/ugol-45-poluotvod-f-250-iz-ocinkovannoj-stali) | Оставить в покупных, если компания фильтры не делает |
| **шкаф** | (1) вытяжной шкаф (лабораторная мебель) — у Plast Product из ПП; (2) шкаф управления (автоматика) | «управления», «автоматики» → (2) | [Plast Product](https://plast-product.ru/shkaf-zont-rechetki) | Добавлять только «шкаф управления» |
| **привод** | (1) ручной привод — часть ПП-клапана; (2) электропривод — покупной (Belimo) | «электро», Belimo, LM24 → (2) | [Спецвент — ДК-ЭП](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/drossel-klapany-s-elektroprivodom.html), [Belimo LM24A](https://blm.spb.ru/product/lm24a/) | Не добавлять «привод» |
| **ВР** | (1) вентилятор радиальный ВР 80-75; (2) виброизолятор резиновый ВР 201/202/203; (3) подстрока «вр» в словах «врезка», «КВР» | — | [Вента](https://venta-nt.ru/catalog/ventilyaciya/promyishlennyie-ventilyatoryi-obschie-svedeniya/oboznachenie-ventilyatorov), [Виавент](https://viavent.ru/products/vozd/vibroizolyatory/) | Не добавлять голое «вр». Добавлять с цифрами: «вр 80», «вр-80», «вр 280» |
| **Ф / ф** | (1) диаметр («Клапан обратный КО Ф100»); (2) фланец плоский «Ф», «Фу»; (3) фальцевое исполнение «Ф» в РД 95 933-91; (4) часть «ФВГ» | «Ф» после размера через дефис («560-Ф») → фланец | [Неватом — КО](https://www.nevatom.ru/catalog/klapany_obratnye_ko_babochka/), [Спецвент](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/obratnye-klapany.html), [РД 95 933-91](https://files.stroyinf.ru/Data2/1/4293735/4293735461.pdf) | «ф20» после прямоугольного сечения не считать диаметром (Q40 — спросить) |
| **Р** | (1) раструб (Спецвент); (2) «на рамках» (РД 95 933-91) | — | [Спецвент PDF](https://specvent.com/assets/files/2025/katalog-specialnaya-ventilyaciya.pdf), [РД 95 933-91](https://files.stroyinf.ru/Data2/1/4293735/4293735461.pdf) | — |
| **вентилятор** (как подстрока) | (1) сам вентилятор — покупной; (2) упоминание в описании чужой позиции: «(входное сечение вентилятора)», «переход … к вентилятору», «гибкие вставки для вентиляторов» | Слово в скобках или после «для», «к», «сечение» → не вентилятор | (внутр.), [SPB Active](http://spbactive.ru/production/airducts/) | См. раздел 4.4 |
| **сетка / решётка** | ПП-решётка (своё) против покупной металлической. Для металлических решёток марки не собирались (не проверено) | — | [Спецвент — решётки](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/reshetki-kruglye.html) | — |
| **колпак** | Деталь зонта («1 — Колпак») или дефлектор («Дефлекторный колпак») | — | [серия 5.904-51](https://files.stroyinf.ru/Data2/2/4294852/4294852971.pdf), [SPB Active](http://spbactive.ru/production/airducts/) | — |

---

## 3. Обозначения размеров, толщин, длин, углов и единиц

### 3.1. Диаметр

| Запись | Значение | Пример | Источники | Риск для разбора |
|---|---|---|---|---|
| «⌀» (знак диаметра), «Ø», «∅» | Диаметр | ГОСТ 2.307-2011, п. 5.38: «При указании размера диаметра (во всех случаях) перед размерным числом наносят знак» ⌀. На сайте spds.ru знак показан как «Æ»: это шрифт Symbol | [ГОСТ 2.307-2011 (spds.ru)](https://www.spds.ru/info/standarts/2.307-2011/part5.html) | После конвертации DOC или PDF знак может прийти как «Æ» (вывод) — добавить в синонимы |
| «ф», «Ф», «ф 250», «Ф100» | Диаметр (клавиатурная замена) | «Полуотвод (угол 45) ф 250»; «Клапан обратный КО Ф100» | [Вент-Стайл](https://www.vent-style.ru/goods/ugol-45-poluotvod-f-250-iz-ocinkovannoj-stali), [Неватом — КО](https://www.nevatom.ru/catalog/klapany_obratnye_ko_babochka/) | «Ф» — ещё и фланец (раздел 2) |
| «d», «D», «D1--D2», «D100-D100-D100» | Диаметр. У Спецвента D — «наружный (внешний) диаметр» | «Переход ПП 560--630-Фу»; «Тройник Y (штаны) D160-D160-D160» | [Спецвент — переходы](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/perehody1.html), [ВентКом](https://ventkom.com/fasonnye-izdeliya-dlya-spiralno-navivnyh-vozduhovodov/trojnik-y-shtany/) | У серии 5.904-51 «До» — патрубок, «Д» — купол зонта |
| «da» (DE), «Φ» (греческая буква, EN из Китая) | Наружный диаметр | «da 50 bis da 1.250 mm»; «Φ63-3000mm» | [SR](https://www.sr-kunststofftechnik.de/drosselklappen.html), [XICHENG](https://air-emissions.com/pps-ducting-and-fittings) | Греческая «Φ» ≠ кириллическая «Ф» (вывод) |
| «DN», «Ду» | Номинальный диаметр (условный проход) | ГОСТ 21.602, п. 4.9: для арматуры — «DN». Для трубопроводов и воздуховодов — «⌀» или «DN». Для «наружного диаметра и толщины стенки» — «⌀» («⌀76х3») | [ГОСТ 21.602-2016](https://www.eng-in.ru/images/spravka/normativ/GOST-21.602-2016.pdf) | У ПП размер задают по наружному диаметру. «DN» у клиента может означать и условный проход трубы (вывод) |
| Ряд диаметров | У ПП есть ⌀110, 180, 225 (ряд труб). У стали обычно ⌀100 | Тетра: «диаметр от 110 до 2000 мм». У Спецвента ряд D крышных зонтов: 110, 160, 180, 200, 225, 250, 315, 355, 400, 450, 500, 560, 630, 710, 800, 900, 1000, 1200…2100. Второе число в строке таблицы — высота H, а «70» — длина раструба или муфты до D355. Стальные: «КО Ф100», «D100» | [Тетра](https://prom-emkosti.ru/produktsiya/himstojkie-vozduhovody/vozduhovody-iz-polipropilena/), [Спецвент — зонты](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/zonty-kryshnye.html), [Неватом — КО](https://www.nevatom.ru/catalog/klapany_obratnye_ko_babochka/) | «ф100» в ПП-запросе может означать 110 (вывод). Задавать вопрос, не подменять |

### 3.2. Прямоугольное сечение

| Запись | Значение | Источники | Риск |
|---|---|---|---|
| «AxB», «А×В», «АхВ», «560×560» | Ширина × высота | [Спецвент PDF](https://specvent.com/assets/files/2025/katalog-specialnaya-ventilyaciya.pdf), [Спецвент — перекидные](https://specvent.com/katalog/ventilyaciya-pryamougolnogo-secheniya/perekidnye-klapany.html) | «х» бывает латинской x, кириллической х или знаком ×; все три надо принимать (вывод) |
| «ВхН=250х400» | B — ширина, H — высота | [РД 95 933-91](https://files.stroyinf.ru/Data2/1/4293735/4293735461.pdf) | — |
| «140*140», «900/300*500» | «*» вместо «х»; «/» отделяет магистраль от врезки | [Неватом — вставки](https://www.nevatom.ru/catalog/gibkie_vstavki_vg_vo_vr_kp_vr_vr/), [ТехноВент](https://vektorvent.ru/articles/flancevoe-soedinenie-vozduhovodov/) | «*» — умножение, а не сноска (вывод) |
| Порядок сторон | ГОСТ 21.602, п. 4.9: для горизонтальных воздуховодов на планах «сначала приводят ширину воздуховода и после знака „х“ — его высоту». На форуме спорят, какой размер первый у отводов | [ГОСТ 21.602-2016](https://www.eng-in.ru/images/spravka/normativ/GOST-21.602-2016.pdf), [форум АВОК](https://forum.abok.ru/lofiversion/index.php/t97255.html) (форум) | Для площади порядок не важен, для отводов важен |
| «d×S», «d х S х L» | Диаметр × толщина стенки (× длина), **а не прямоугольник**. Примеры: «Воздуховод ПП d х S х L»; «Отвод 90° ПП 470×4-Фу»; «Шумоглушитель ПП 535×5-Фу»; ГОСТ 21.602: «⌀76х3» | [Спецвент PDF](https://specvent.com/assets/files/2025/katalog-specialnaya-ventilyaciya.pdf), [Спецвент — отводы](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/otvody.html), [Спецвент — глушители](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/shumoglushiteli.html) | **Высокий.** Если второе число ≤ 20 и стоит слово «ПП» или «⌀», это толщина (вывод) |

### 3.3. Толщина стенки

| Запись | Источники | Примечание |
|---|---|---|
| «S» («S — толщина стенки, мм»; «толщиной стенки S = 0,5–1,0 мм») | [Спецвент PDF](https://specvent.com/assets/files/2025/katalog-specialnaya-ventilyaciya.pdf), [РД 95 933-91](https://files.stroyinf.ru/Data2/1/4293735/4293735461.pdf) | — |
| «s=5 mm» (DE) | [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1) | По ЕСКД толщину плоской детали указывают буквой s (ГОСТ 2.307-2011, п. 5.57, рис. 78; сама буква на рисунке, в тексте пункта её нет — не проверено) — [spds.ru](https://www.spds.ru/info/standarts/2.307-2011/part5.html) |
| «t» («Толщина заслонки мм t») | [Спецвент PDF](https://specvent.com/assets/files/2025/katalog-specialnaya-ventilyaciya.pdf) | — |
| «δ=3», «б=3 мм» | (внутр.) строки клиентов | «б» — кириллическая замена греческой «δ» (вывод) |
| «толщина стенки 3–10 мм», «толщиной от 2 до 10 мм» | [POLEX PDF](https://polex-vent.ru/uploads/promotional/file/2/Ventilyatsiya.pdf), [Полиюнион](https://polyunion.ru/ventilyatsionnye-sistemy/vozduhovody-ventiljacija-iz-polipropilena) | Реальный диапазон для ПП-листа. Толщина вне 2–25 мм — повод для вопроса (вывод) |

### 3.4. Длина

| Запись | Источники | Примечание |
|---|---|---|
| «L» — «строительная длина воздуховода, мм» | [Спецвент PDF](https://specvent.com/assets/files/2025/katalog-specialnaya-ventilyaciya.pdf) | — |
| «L=», «L-1500мм», «L- 500мм», «L1500» | (внутр.) | Дефис после L — не минус (вывод) |
| «длиной 500, 1000, 1500, 2000, 2500, 3000 мм»; «standard lengths of 1.0 m, 1.5 m, 2.0 m, and 3.0 m» | [POLEX](https://polex-vent.ru/katalog/vozduhovody-iz-polipropilena), [XICHENG](https://air-emissions.com/pps-ducting-and-fittings) | Типовые длины прямых. Нарезка метража — открытый вопрос Q37 |
| «Kulissenlänge 500 mm», «Muffler: 1250mm Long» | [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1), [Simtech](https://www.simtechusa.com/products-and-services/air-handling/at-polypropylene-duct-systems) | Длина шумоглушителя |

### 3.5. Углы и ответвления

| Запись | Источники | Примечание |
|---|---|---|
| «90°», «45°», «β°» («Отвод β° ПП D × S»), «с центральным углом 90°» | [Спецвент — отводы](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/otvody.html), [РД 95 933-91](https://files.stroyinf.ru/Data2/1/4293735/4293735461.pdf) | — |
| «угол 45», «Полуотвод (угол 45)» | [Вент-Стайл](https://www.vent-style.ru/goods/ugol-45-poluotvod-f-250-iz-ocinkovannoj-stali) | — |
| «90 гр.», «90град», «ф250-90гр.», «под углом 45 гр.» | (внутр.) | «-90гр» — угол, а не отрицательное число. «под углом 45» в строке тройника — угол ответвления (вывод) |
| «ОТВОД 45 О» — знак «°» распознан как буква «О» | [POLEX PDF](https://polex-vent.ru/uploads/promotional/file/2/Ventilyatsiya.pdf) | Артефакт извлечения текста из PDF (вывод) |
| «45° Abgang», «45° Lateral», «45° Wye» | [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1), [Simtech](https://www.simtechusa.com/products-and-services/air-handling/at-polypropylene-duct-systems) | — |
| Ответвление: «560--400--560» (магистраль–ответвление–магистраль), «⌀250-⌀160», «ф250/ф160/ф250», «D160-D160-D160», «900/300*500» | [Спецвент — тройники](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/trojniki.html), [ВентКом](https://ventkom.com/fasonnye-izdeliya-dlya-spiralno-navivnyh-vozduhovodov/trojnik-y-shtany/), [ТехноВент](https://vektorvent.ru/articles/flancevoe-soedinenie-vozduhovodov/) | При двух числах меньшее — ответвление. При трёх среднее — ответвление (вывод) |

### 3.6. Количество и единицы

| Запись | Значение | Источники | Риск |
|---|---|---|---|
| «м» (ОКЕИ 006), «пог.м» (ОКЕИ 018) | Метр, погонный метр | [ОКЕИ](https://standards.narod.ru/ok/okei.htm) | — |
| «мп», «м.п.», «п.м.», «пог. м», «пог.м», «1 пог. метр», «спецификация в пог.м» | Погонные метры прямого воздуховода | [ПластПлэнт](https://plastplant.ru/plastikovye-vozduhovody/), [Полиюнион](https://polyunion.ru/ventilyatsionnye-sistemy/vozduhovody-ventiljacija-iz-polipropilena), (внутр.) | «2 мп» и «2 шт» дают разное число изделий. Нарезка — Q37 |
| «м2», «кв.м» (ОКЕИ 055) | Квадратные метры — **площадь, а не длина**. Проектировщики дают воздуховоды в м² с надбавкой: «На всю остальную фасонину даем 20 процентов добавки в м2 в воздуховодах. Переходы — 2 процента…» (форум) | [ОКЕИ](https://standards.narod.ru/ok/okei.htm), [форум АВОК](https://forum.abok.ru/lofiversion/index.php/t97255.html) | Строки в м² нельзя трактовать как метры. Пересчёт делает код, не модель |
| «шт», «шт.» (ОКЕИ 796), «компл» (ОКЕИ 839), «набор» (ОКЕИ 704) | Штуки, комплекты | [ОКЕИ](https://standards.narod.ru/ok/okei.htm) | «к-т» как сокращение комплекта в ОКЕИ нет (не проверено) |
| Графа «Ед. измерения» в спецификации | По ГОСТ 21.110-2013 в неё пишут «обозначение единицы измерения» | [ГОСТ 21.110-2013](https://stv39.ru/upload/pdf/%D0%A1%D1%82%D1%80%D0%BE%D0%B8%D1%82%D0%B5%D0%BB%D1%8C%D0%BD%D0%BE%D0%B5%20%D0%BE%D0%B1%D0%BE%D1%80%D1%83%D0%B4%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5,%20%D0%BE%D1%81%D0%BD%D0%B0%D1%81%D1%82%D0%BA%D0%B0%20%D0%B8%20%D0%BC%D0%B0%D1%82%D0%B5%D1%80%D0%B8%D0%B0%D0%BB%D1%8B/%D0%A1%D1%82%D1%80%D0%BE%D0%B8%D1%82%D0%B5%D0%BB%D1%8C%D0%BD%D0%BE%D0%B5%20%D0%BE%D0%B1%D0%BE%D1%80%D1%83%D0%B4%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5.pdf) | В XLSX единица часто стоит в отдельной колонке (вывод) |
| «№ 2,5», «№ 6,3», «ВР 80-75-4» | Номер вентилятора — диаметр колеса в дециметрах | [Вента](https://venta-nt.ru/catalog/ventilyaciya/promyishlennyie-ventilyatoryi-obschie-svedeniya/oboznachenie-ventilyatorov) | «№4» — не количество и не диаметр воздуховода |

### 3.7. Коды соединений и исполнений

| Код | Значение | Источники |
|---|---|---|
| «Ф», «Фу», «Р», «М» в конце («Зонт крышный ПНД 560-Фу») | Фланец плоский, фланец под уплотнение, раструб, муфта | [Спецвент PDF](https://specvent.com/assets/files/2025/katalog-specialnaya-ventilyaciya.pdf), [Спецвент — зонты](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/zonty-kryshnye.html) |
| «ПП-ЭП» | Исполнение с площадкой под электропривод | [Спецвент — ДК-ЭП](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/drossel-klapany-s-elektroprivodom.html) |
| «ФЛ», «Б», «Р», «ФЛ/Б»… и «Ф», «С» | Соединение: фланцевое, бандажное, на рамках. Изготовление: фальцевый, сварной (стальные воздуховоды) | [РД 95 933-91](https://files.stroyinf.ru/Data2/1/4293735/4293735461.pdf) |
| «раструб/труба», «труба/фланец20» | Торцы изделия. Открытые вопросы Q41 и Q40 | (внутр.) |

### 3.8. Заголовки систем и марки элементов

| Что | Значение | Источники |
|---|---|---|
| П, В, У, А, К, ДП, ДВ, ПУ, ПЕ, ВЕ, ДПЕ, ДВЕ + номер («П1, В1, ВЕ1, К1») | Марки систем: приточная, вытяжная, завеса, отопительный агрегат, кондиционирование, противодымные приточная и вытяжная, пылеудаление; «Е» — естественное побуждение | [ГОСТ 21.602-2016, табл. 1](https://www.eng-in.ru/images/spravka/normativ/GOST-21.602-2016.pdf) |
| Ст, ГСт, ГВ, КП, КР, ЛП, ЛВ, О + номер | Марки элементов: стояки, ветвь, компенсатор, крепление (опора), лючок для замеров, лючок для чистки, местный отсос | [ГОСТ 21.602-2016, табл. 2](https://www.eng-in.ru/images/spravka/normativ/GOST-21.602-2016.pdf) |
| Заголовок раздела в графе «Наименование» | «Наименования частей, разделов и подразделов записывают в графе „Наименование и техническая характеристика“ в виде заголовка» | [ГОСТ 21.110-2013](https://stv39.ru/upload/pdf/%D0%A1%D1%82%D1%80%D0%BE%D0%B8%D1%82%D0%B5%D0%BB%D1%8C%D0%BD%D0%BE%D0%B5%20%D0%BE%D0%B1%D0%BE%D1%80%D1%83%D0%B4%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5,%20%D0%BE%D1%81%D0%BD%D0%B0%D1%81%D1%82%D0%BA%D0%B0%20%D0%B8%20%D0%BC%D0%B0%D1%82%D0%B5%D1%80%D0%B8%D0%B0%D0%BB%D1%8B/%D0%A1%D1%82%D1%80%D0%BE%D0%B8%D1%82%D0%B5%D0%BB%D1%8C%D0%BD%D0%BE%D0%B5%20%D0%BE%D0%B1%D0%BE%D1%80%D1%83%D0%B4%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5.pdf) |
| Импортное оборудование | «записывают с теми наименованиями и обозначениями, которые содержатся в сопроводительной технической документации». Поэтому в спецификациях латиница: Belimo, LM24A | [ГОСТ 21.110-2013, п. 4.9](https://stv39.ru/upload/pdf/%D0%A1%D1%82%D1%80%D0%BE%D0%B8%D1%82%D0%B5%D0%BB%D1%8C%D0%BD%D0%BE%D0%B5%20%D0%BE%D0%B1%D0%BE%D1%80%D1%83%D0%B4%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5,%20%D0%BE%D1%81%D0%BD%D0%B0%D1%81%D1%82%D0%BA%D0%B0%20%D0%B8%20%D0%BC%D0%B0%D1%82%D0%B5%D1%80%D0%B8%D0%B0%D0%BB%D1%8B/%D0%A1%D1%82%D1%80%D0%BE%D0%B8%D1%82%D0%B5%D0%BB%D1%8C%D0%BD%D0%BE%D0%B5%20%D0%BE%D0%B1%D0%BE%D1%80%D1%83%D0%B4%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5.pdf) |
| Изделия индивидуального изготовления | Графы «Тип, марка…» и «Код продукции» не заполняют | [ГОСТ 21.110-2013, п. 4.8](https://stv39.ru/upload/pdf/%D0%A1%D1%82%D1%80%D0%BE%D0%B8%D1%82%D0%B5%D0%BB%D1%8C%D0%BD%D0%BE%D0%B5%20%D0%BE%D0%B1%D0%BE%D1%80%D1%83%D0%B4%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5,%20%D0%BE%D1%81%D0%BD%D0%B0%D1%81%D1%82%D0%BA%D0%B0%20%D0%B8%20%D0%BC%D0%B0%D1%82%D0%B5%D1%80%D0%B8%D0%B0%D0%BB%D1%8B/%D0%A1%D1%82%D1%80%D0%BE%D0%B8%D1%82%D0%B5%D0%BB%D1%8C%D0%BD%D0%BE%D0%B5%20%D0%BE%D0%B1%D0%BE%D1%80%D1%83%D0%B4%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5.pdf) |

Признак на практике: у покупного оборудования заполнена графа «Тип, марка» (ВР 80-75, КПУ-1М, LM24A), у ПП-изделий индивидуального изготовления она пустая. Это может помочь классификатору (вывод).

### 3.9. Справка к открытому вопросу Q38: зонт с одним размером

По типовой серии 5.904-51 (стальные зонты ЗК.00.000) пары «патрубок До → купол Д» такие: 200→350, 250→450, 315→550, 400→700, 450→800, 500→900, 710→1300, 800→1450, 1000→1800, 1250→2250. Купол составляет примерно **1,75–1,83 × патрубок** ([серия 5.904-51](https://files.stroyinf.ru/Data2/2/4294852/4294852971.pdf)). Строка для 630 распознана плохо и не учтена. У дефлекторов: Д 315 → Д1 510, 400→730, 500→950, 630→1190, 1000→2000. Черновое правило Q38 — «купол = 2 × патрубок». Это справка, **не решение**: вопрос Q38 открыт, решает руководитель.

---

## 4. Покупные позиции: ключевые слова (подстроки в нижнем регистре)

### 4.1. Что такое ФВГ

- **ФВГ — «фильтры волокнистые гальванические».** Предназначены «для высокоэффективной очистки воздушных вентиляционных выбросов от жидких и растворимых в воде твердых аэрозольных частиц и паров в гальванических, травильных и химических производствах; из вытяжных шкафов, лабораторных помещений». Исполнения корпуса: ФВГ-ПНД, ФВГ-ПВХ, ФВГ-ПП, ФВГ-Т (титан), ФВГ-М (нержавеющая сталь). ФКГ — «фильтр кассетный гальванический». На сайте встречается опечатка «ФГВ» — пример того, как пишут на практике. Источник: [Plast Product](https://plast-product.ru/filtryi-voloknistyie-galvanicheskie/).
- **ФВГ-Т** — корпус «из стойкого к агрессивному воздействию титана». Очищает воздух с каплями электролита и туманом «от смеси серной и хромовой кислот» ([Кондор-Эко](https://kondor-eco.ru/product/82-voloknistye-filtry-tipa-fvg-t.html)).
- **ФВГ/ФВА** — «Фильтры волокнистые гальванические (аэрозольные)» с «каплеотбойными кассетами из полипропилена ПП и полиэтилена ПНД». Типоразмеры ФВА-П-5000 … ФВА-П-40000 указаны по производительности в м³/ч ([Спецвент](https://specvent.com/katalog.html), [Спецвент — ФВА](https://specvent.com/filtr-fva.html)).
- **ФВГ-ПП-УА** — «аналоги фильтров ФВГ-Т и ФВГ-М» из ПП ([УралАктив](https://uralactiv.ru/gazoochistnoe-oborudovanie/voloknistye-filtry-fvg/)).
- Вывод: для ameri ФВГ — покупное оборудование (по заданию). Но часть ПП-производителей делает ФВГ сама. Если компания начнёт делать корпуса ФВГ, «фвг» надо убрать из покупных.

### 4.2. Проверка текущего списка

Ключевые слова из `params.yaml` дописываются к кортежам прототипа (`actions._install_harness`) и приводятся к нижнему регистру. Текст позиции прототип, по описанию, тоже переводит в нижний регистр. Приводит ли он «ё» к «е», неизвестно: прототипа нет в репозитории.

| Слово (сейчас) | Почему покупное | Пример строки | Риск ложного срабатывания | Рекомендация |
|---|---|---|---|---|
| «гибкая вставка», «гибкие вставки» | Виброизолирующая вставка из ткани между вентилятором и сетью ([Неватом](https://www.nevatom.ru/catalog/gibkie_vstavki_vg_vo_vr_kp_vr_vr/), [Аэрдин](https://aerdyn.ru/gibkie-vstavki/)) | «Гибкая вставка 250х250» (внутр.) | Низкий. **Пропуск:** «Вставка гибкая ВГ-…», «вибровставка» | Оставить и добавить «вставка гибкая», «вставки гибкие», «вибровставк» |
| «хомут» | Стальной хомут с резинкой, крепёж | «Хомут ф250 с резинкой» (внутр.) | Низкий | Оставить |
| «виброизолятор» | ДО-38…ДО-45 (пружинные), ВР 201–203 (резиновые) для вентиляторов ([Неватом](https://www.nevatom.ru/catalog/vibroizolyatory_vr/), [Виавент](https://viavent.ru/products/vozd/vibroizolyatory/)) | «Виброизолятор ДО-38» | Низкий | Оставить |
| «вентилятор» | Для ameri вентиляторы покупные | «Вентилятор ВР 80-75 №4» | **Средний–высокий:** «Защитная сетка ⌀250 (входное сечение вентилятора)», «Переход … к вентилятору», «гибкие вставки для вентиляторов» ([SPB Active](http://spbactive.ru/production/airducts/)) | Оставить, но проверять после ключевых слов своих изделий (решётка, сетка, переход, отвод) или только в начале наименования. Проверить порядок в прототипе |
| «скруббер» (в прототипе) | Мокрая очистка газов. Для ameri покупное | «Скруббер …» | Низкий. Спецвент делает «Скрубберы из пластика», но для ameri — покупное | Оставить |
| «фильтр» (в прототипе) | ФВГ, ФВА, ФКГ, канальные фильтры | «Фильтр ФВГ-Т» | Низкий, если компания фильтры не делает | Оставить и добавить «фвг», «фва», «фкг» (на случай строки без слова «фильтр») |
| «короб» (в прототипе) | Непонятно; вероятно, кабельный или шумоизолирующий короб (не проверено) | «Короб ПП 600х300» — это **своё** изделие | **Высокий** ([ПластПлэнт](https://plastplant.ru/plastikovye-vozduhovody/), [Полимеризделия](https://izpolimera.ru/vozduhovodi-polipropilen/)) | **Убрать** или заменить на «кабельный короб», «кабель-канал» |

### 4.3. Предлагаемое пополнение

| Ключевое слово | Почему покупное | Пример строки | Риск ложного срабатывания | Рекомендация |
|---|---|---|---|---|
| «вставка гибкая», «вставки гибкие», «вибровставк» | Та же гибкая вставка, другой порядок слов | «Вставка гибкая ВГ-140*140-У-О» ([Неватом](https://www.nevatom.ru/catalog/gibkie_vstavki_vg_vo_vr_kp_vr_vr/)); «Гибкая вставка (вибровставка)» ([Градвент](https://gradvent.com/komplektuyushchie/gibkaya-vstavka)) | Низкий | **Добавить** |
| «фвг», «фва», «фкг» | Волокнистые фильтры (раздел 4.1) | «ФВГ-Т 0,74» | Низкий: короткие коды, в обычных словах не встречаются (вывод) | **Добавить** |
| «абсорбер» | Аппараты мокрой очистки, родственные скрубберу («Абсорбционные фильтры с массообменной насадкой», [Спецвент](https://specvent.com/katalog.html)) | «Абсорбер …» | Низкий | Добавить |
| «квр» | Стальной регулирующий клапан ([МаксАэро](https://www.maxaero.by/katalog-produkcii/sobstvennoe-proizvodstvo/zaslonki-vozdushnye/klapan-vozdushnyy-reguliruyushchiy-tipa-kvr)) | «Клапан КВР 400х400 с электроприводом» | Низкий | **Добавить** |
| «кпу», «клоп», «огнезадерж», «противопожар», «дымоудал» | Противопожарные клапаны: КПУ-1М «огнезадерживающий клапан» ([МашПром](https://www.mashprom.org/ventilyacyonnoe_oborudovanie/klapan_protivopozharnyj_kpu_1_kpu_2_kpu_3/)); «КЛОП-1 60 НЗ с приводом Belimo» ([Панорама](https://panoramavent.ru/product/protivopozharnye-klapany/ognezaderzhivayushhie-klapany/klapan-ognezaderzhivayushhij-kom-1-dlya-protivodymnoj-ventilyacii/)). КОМ-1 назван огнезадерживающим клапаном только в заголовке выдачи поиска (не проверено) | «Клапан КПУ-1М 250 НО» | Низкий. ПП-клапанов этих типов у ПП-производителей не найдено (вывод) | **Добавить**. Можно добавить «ком-1» (не проверено) |
| «belimo», «lm24», «электропривод» | Привод заслонки: Belimo LM24A — «Привод воздушной заслонки» ([Belimo LM24A](https://blm.spb.ru/product/lm24a/)) | «Электропривод Belimo LM24A» | **Средний:** «Дроссель-клапан ПП-ЭП … с площадкой под электропривод» — ПП-корпус свой ([Спецвент](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/drossel-klapany-s-elektroprivodom.html)) | Добавлять только после решения руководителя: вся строка покупная или делится на корпус и привод |
| «ирисов» | Ирисовый клапан, сталь ([РОВЕН](https://rowen.ru/catalog/ventilyatsionnye_klapany/klapany_irisovye/)) | «Клапан ирисовый SPI 250» | Низкий | Добавить |
| «гтк», «гтп» | Стальные трубчатые шумоглушители по серии 5.904-17 ([Интеркон](http://intercon.com.ua/wp-content/uploads/2019/06/GTK-GTP-GP-min.pdf)) | «Глушитель трубчатый ГТК 1-4 (А7Е 186.000-03) D 315» | Низкий | Добавить. Голое «шумоглушител» не добавлять — см. 4.4 |
| «вр 80», «вр-80», «вр 280», «вр-280», «вц 4», «вц-4», «вц 14», «вкр», «врп» | Марки вентиляторов: «В — вентилятор; Р или Ц — радиальный или центробежный» ([Вента](https://venta-nt.ru/catalog/ventilyaciya/promyishlennyie-ventilyatoryi-obschie-svedeniya/oboznachenie-ventilyatorov)). ВРП 280-46 и ВРП 80-75 — пластиковые ([Спецвент](https://specvent.com/ventilyatory.html), [Plast Product](https://plast-product.ru/ventilyatoryi-promyishlennyie/ventilyatory-iz-polipropilena/)) | «ВР 80-75 №4 К1» (исполнения К1, Ж2, В — по выдаче поиска, не проверено) | Низкий при записи с цифрами. Голое «вр» ловит «врезка» и «КВР» | Добавить с цифрами. «вкр» пересекается с «вкруг» и «вкрутить» (вывод) — риск малый |
| «электродвигател», «двигател», «мотор» | Электродвигатель вентилятора или насоса (в каталоге вентиляторов графа «Электродвигатель», [Спецвент PDF](https://specvent.com/assets/files/2025/katalog-specialnaya-ventilyaciya.pdf)) | «Электродвигатель АИР 80» (пример условный) | Низкий | Добавить |
| «насос» | Насос орошения скруббера или ФВГ (вывод) | «Насос химстойкий …» | Низкий | Добавить |
| «шкаф управления», «щит управления», «щит автоматики», «автоматик», «частотн», «преобразовател», «датчик», «контроллер» | Автоматика и электрика («Автоматизация систем вентиляции» — отдельное направление, [SPB Active](http://spbactive.ru/production/airducts/)) | «Шкаф управления вентилятором» | Низкий. **Голое «щит» нельзя:** ловит «за**щит**ная сетка». Голое «шкаф» ловит ПП-«вытяжной шкаф» ([Plast Product](https://plast-product.ru/shkaf-zont-rechetki)) | Добавить только составные слова |
| «шпильк», «анкер», «дюбел», «траверс», «подвес», «струбцин», «перфолент», «крепеж», «крепёж» | Монтажный крепёж: «хомут+струбцина+шпилька умноженное на 400 шт» ([форум АВОК](https://forum.abok.ru/lofiversion/index.php/t97255.html), форум); стальные хомуты и шпильки к ПП-опорам ([XICHENG](https://air-emissions.com/pps-ducting-and-fittings)) | «Шпилька М8 L=1000» | Низкий. «кронштейн» и «опора» не добавлять: ПП-производители делают кронштейны к бортотсосам ([Спецвент](https://specvent.com/bortovye-otsosy-iz-polipropilena-i-polietilena-dlya-galvanicheskih-vann.html)) | Добавить. Писать оба варианта «крепеж/крепёж» или нормализовать «ё» |
| «болт м», «гайк», «шайб» | Метизы | «Болт М10х40» | **Голое «болт»** ловит «отверстиями под болтовое соединение» ([Спецвент](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/zonty-kryshnye.html)) | Добавить только в таком виде |
| «прокладк», «уплотнител», «герметик», «клей» | Расходные материалы | «Прокладка EPDM» | Низкий. «уплотнител» не ловит «фланец под уплотнение» (проверено скриптом) | Добавить после согласования: POLEX продаёт «уплотнительные прокладки» в составе поставки ([POLEX](https://polex-vent.ru/katalog/vozduhovody-iz-polipropilena)) |
| «калорифер», «нагревател», «охладител», «приточная установка», «рекуператор» | Стальное оборудование сети («Канальные нагреватели электрические…», [Вент-Стайл](https://www.vent-style.ru/goods/ugol-45-poluotvod-f-250-iz-ocinkovannoj-stali)) | «Нагреватель канальный …» | Низкий | Добавить |
| «гибкий воздуховод», «шланг» | Покупные гибкие рукава («PVC Spiralschlauch», [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1)) | «Гибкий воздуховод ф160» | Низкий | Добавить |

### 4.4. Не добавлять или добавлять только после решения руководителя

| Слово | Почему нельзя | Источники |
|---|---|---|
| «клапан» | Поймает дроссель-клапан, обратный и перекидной клапаны из ПП — это своё | [Спецвент](https://specvent.com/katalog.html), (внутр.) |
| «привод» | «с ручным приводом» — часть ПП-клапана | [SR](https://www.sr-kunststofftechnik.de/drosselklappen.html) |
| «вставк» | Сейчас ловит только гибкие вставки, но слово слишком общее (вывод) | — |
| «каплеуловител» | ПП-производители делают каплеуловители сами; компания тоже может | [SPB Active](http://spbactive.ru/production/airducts/), [ПластПП](https://msk.plastpp.ru/cleaning-system/drop-traps/), [Нева-Актив](https://npo-neva-aktiv.ru/kapleuloviteli/) |
| «шумоглушител», «глушител» | ПП-шумоглушители — продукция ПП-производителей | [Спецвент](https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/shumoglushiteli.html), [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1) |
| «компенсатор» | Есть ПП «Компенсатор длины» | [SPB Active](http://spbactive.ru/production/airducts/) |
| «диффузор», «конфузор» | Омонимы (раздел 2) | [Plast Product](https://plast-product.ru/promyshlennye-diffuzory-plastikovye) |
| «шкаф», «щит», «болт» без уточнения | Ложные срабатывания: вытяжной шкаф из ПП, «защитная», «болтовое соединение» | — |
| «решетк», «сетк» как покупные | Это ПП-решётки, у них своё правило цены (`grid_keywords`) | (внутр.) |
| «кронштейн», «опора» | ПП-опоры и кронштейны бывают своими | [Спецвент](https://specvent.com/bortovye-otsosy-iz-polipropilena-i-polietilena-dlya-galvanicheskih-vann.html), [XICHENG](https://air-emissions.com/pps-ducting-and-fittings) |
| «до-3», «до-4» (виброизоляторы ДО) | «до» — предлог. Виброизоляторы и так ловятся словом «виброизолятор» (вывод) | — |

### 4.5. Проверка подстрок скриптом

Скрипт `research/A/kw_test.py` прогоняет подстроки по 35 строкам «своих» изделий (строки клиентов из задания и обозначения из каталогов) и 22 строкам покупных. Ложные срабатывания на своих изделиях:

- «вентилятор» → «Защитная сетка ⌀250 (входное сечение вентилятора)», «Переход ф250/250х250 к вентилятору».
- «клапан» → все 5 ПП-клапанов (дроссель-, обратный, перекидной, ПП-ЭП).
- «короб» → «Короб ПП 600х300».
- «щит» → «Защитная сетка …».
- «шкаф» → «Вытяжной шкаф из полипропилена».
- «болт» → «… фланцами под болтовое соединение».
- «привод» → «Дроссель-клапан ПП ф250 с ручным приводом».
- «шумоглушител», «каплеул», «компенсатор» → соответствующие ПП-изделия.

Без ложных срабатываний на этой выборке: все слова из черновика в разделе 4.7. Среди них «вставка гибкая», «вибровставк», «фвг», «фва», «фкг», «квр», «кпу», «клоп», «дымоудал», «ирисов», «гтк», «гтп», «вр 80», «вц 4», «врп», «электродвигател», «насос», «шкаф управления», «щит управления», «автоматик», «частотн», «датчик», «шпильк», «анкер», «травер», «струбцин», «крепеж», «калорифер», «нагревател», «гибкий воздуховод». Кандидаты «уплотнител», «прокладк», «гайк», «шайб», «болт м», «belimo», «lm24» тоже не сработали. «уплотнител» не ловит «Фланец под уплотнение», а более короткое «уплотн» ловит. Выборка маленькая, поэтому это проверка на явные ошибки, а не доказательство.

### 4.6. Замечания к механизму подстрок (вывод)

1. **Порядок правил.** Правила своих изделий (решётка, сетка, переход, отвод, тройник) должны срабатывать раньше покупных, иначе упоминание вентилятора в описании уносит строку в покупные. Порядок проверки в прототипе проверить.
2. **Буква «ё».** Нормализовать «ё» → «е» и в тексте, и в словах, или писать оба варианта.
3. **Порядок слов и словоформы.** «Вставка гибкая» и «гибкая вставка»; «виброизоляторы», «хомуты» подстроки уже ловят.
4. **Смешанные позиции** («ПП-клапан + электропривод», «вентилятор с гибкой вставкой и виброизоляторами»). Нужно отдельное правило: предупреждение и вопрос руководителю, а не молчаливый перенос.
5. **Покупные часто узнаются по графе «Тип, марка» и латинице** (Belimo, LM24A, КПУ-1М, ВР 80-75). Это можно передать модели как признак (ГОСТ 21.110, п. 4.8–4.9).

### 4.7. Черновик для `params.yaml` (не применён; нужно утверждение руководителя)

```yaml
passthrough_keywords:
  # есть
  - гибкая вставка
  - гибкие вставки
  - хомут
  - виброизолятор
  - вентилятор        # проверять после grid/своих изделий (см. 4.6)
  # предложено
  - вставка гибкая
  - вставки гибкие
  - вибровставк
  - фвг
  - фва
  - фкг
  - абсорбер
  - квр
  - кпу
  - клоп
  - огнезадерж
  - противопожар
  - дымоудал
  - ирисов
  - гтк
  - гтп
  - вр 80
  - вр-80
  - вр 280
  - вр-280
  - вц 4
  - вц-4
  - вц 14
  - электродвигател
  - насос
  - шкаф управления
  - щит управления
  - щит автоматики
  - автоматик
  - частотн
  - датчик
  - шпильк
  - анкер
  - дюбел
  - траверс
  - струбцин
  - перфолент
  - крепеж
  - крепёж
  - калорифер
  - нагревател
  - гибкий воздуховод
# под вопросом: belimo, lm24, электропривод, шумоглушител, прокладк, уплотнител, болт м
# убрать из прототипа: короб (или сузить до «кабельный короб»)
```

---

## 5. Что производители ПП-вентиляции обычно делают сами

Все пункты — продукция из собственных перечней ПП-производителей. Своё ли это для ameri, решает руководитель; ассортимент компании в задании дан в общих чертах.

| Изделие | Кто делает из ПП (источник) | Для ameri |
|---|---|---|
| Обратный клапан | Спецвент («Обратный клапан ПП 560-Фу»), Полимеризделия, SPB Active, KWERK, Simtech | Своё (в задании прямо названо) |
| Дроссель-клапан, в том числе «с площадкой под электропривод» | Спецвент, SPB Active, Полимеризделия, SR (DE), KWERK (DE) | Своё. Привод покупной |
| Шибер, шиберная заслонка | Спецвент, ПластПлэнт, Полимеризделия | Своё |
| Перекидной клапан | Спецвент, SPB Active | Вероятно своё (не проверено для компании) |
| Зонт крышный | Спецвент («Зонт крышный ПП/ПНД D»), POLEX, SPB Active | Своё |
| Зонт вытяжной (местный отсос), вытяжная панель | УралАктив, Спецвент (по чертежам), Plast Product | Вероятно своё, но это **другое изделие** с другим расчётом |
| Дефлектор, дефлекторный колпак | SPB Active, Полимеризделия, SR (DE), Simtech | Своё (в задании названо) |
| Решётка (жалюзийная), защитная сетка | Спецвент («Решетка жалюзийная ПП 560-Ф»), SPB Active, KWERK | Своё |
| Бортовой отсос | Спецвент, УралАктив, Полимеризделия, Plast Product | Своё (в задании названо) |
| Каплеуловитель | SPB Active, ПластПП, НПО Нева-Актив, Спецвент (каплеотбойные кассеты ФВА) | Уточнить: часто своё |
| Шумоглушитель ПП | Спецвент, Полимеризделия, KWERK, Simtech | Уточнить |
| Компенсатор длины, узел прохода через кровлю, фланец плоский прижимной, врезка, утка, крестовина, заглушка | SPB Active, Спецвент, POLEX | Своё |
| Гибкие вставки из пластика | Спецвент, SPB Active, KWERK (Wellmanschette), Simtech | Для ameri покупное (по заданию) |
| ФВГ / ФВА | Спецвент, Plast Product, УралАктив | Для ameri покупное (по заданию) |
| Скрубберы, абсорберы | Спецвент, XICHENG | Для ameri покупное (по заданию) |
| Вентиляторы ВРП 280-46, ВРП 80-75, корпуса вентиляторов | Спецвент, Plast Product | Для ameri покупное (по заданию) |
| Вытяжные шкафы, промышленные диффузоры, ёмкости, ванны | Plast Product | Не профиль компании (вывод). Задавать вопрос |

Источники к таблице: [Спецвент](https://specvent.com/katalog.html), [Спецвент PDF](https://specvent.com/assets/files/2025/katalog-specialnaya-ventilyaciya.pdf), [SPB Active](http://spbactive.ru/production/airducts/), [Полимеризделия](https://izpolimera.ru/vozduhovodi-polipropilen/), [ПластПлэнт](https://plastplant.ru/plastikovye-vozduhovody/), [POLEX](https://polex-vent.ru/katalog/vozduhovody-iz-polipropilena), [УралАктив](https://uralactiv.ru/ventilyatsiya-polipropilenovaya/vozduhovody-iz-polipropilena/zonty-vytyazhnye/), [Plast Product](https://plast-product.ru/shkaf-zont-rechetki), [ПластПП](https://msk.plastpp.ru/cleaning-system/drop-traps/), [Нева-Актив](https://npo-neva-aktiv.ru/kapleuloviteli/), [KWERK](https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1), [SR](https://www.sr-kunststofftechnik.de/drosselklappen.html), [Simtech](https://www.simtechusa.com/products-and-services/air-handling/at-polypropylene-duct-systems), [XICHENG](https://air-emissions.com/pps-ducting-and-fittings).

Вопросы руководителю, которые закроют границу «своё / покупное»:
1. Делаем ли ПП-шумоглушители?
2. Делаем ли каплеуловители?
3. Делаем ли гибкие вставки из пластика или только покупаем тканевые?
4. «Дроссель-клапан с электроприводом» — одна строка или «ПП-корпус + покупной привод»?
5. Вытяжные зонты над ваннами — наши? Как их считать?
6. Что прототип имеет в виду под «коробом» в списке покупных?

---

## 6. Источники (дата обращения ко всем — 2026-09-26)

Производители ПП-вентиляции (РФ):
1. Спецвент, каталог — https://specvent.com/katalog.html — перечень изделий, виды соединений, материалы PP-C/PP-H/ПНД, ФВГ/ФВА, гибкие вставки из пластика, ВРП.
2. Спецвент, PDF-каталог 2025 — https://specvent.com/assets/files/2025/katalog-specialnaya-ventilyaciya.pdf — формат «Воздуховод ПП d х S х L», коды Ф/Фу/Р/М, определения отвода, дроссель-клапана и шибера, материалы, ФВА, вентиляторы. Текст извлечён со сдвигом кодировки шрифта.
3. Спецвент, отводы — https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/otvody.html — «отвод (угол, колено)», «Отвод 90° ПП 470×4-Фу».
4. Спецвент, тройники — https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/trojniki.html — «Тройник ПП 560--400--560-Ф», «отвод» как ответвление.
5. Спецвент, переходы — https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/perehody1.html — «Переход ПП 560--630-Фу».
6. Спецвент, дроссель-клапаны и шиберы — https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/shibernye-zaslonki1.html — «Дроссель-клапан ПП 560-Фу».
7. Спецвент, ДК с электроприводом — https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/drossel-klapany-s-elektroprivodom.html — «ПП-ЭП», «площадка под электропривод».
8. Спецвент, обратные клапаны — https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/obratnye-klapany.html
9. Спецвент, решётки — https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/reshetki-kruglye.html — «Решетка жалюзийная ПП 560-Ф».
10. Спецвент, шумоглушители — https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/shumoglushiteli.html — «Шумоглушитель ПП 535×5-Фу».
11. Спецвент, перекидные клапаны — https://specvent.com/katalog/ventilyaciya-pryamougolnogo-secheniya/perekidnye-klapany.html
12. Спецвент, зонты крышные — https://specvent.com/katalog/ventilyaciya-kruglogo-secheniya/zonty-kryshnye.html — D = наружный диаметр, «Зонт крышный ПНД 560-Фу», «фланец шириной 45 мм», ПП-УФ.
13. Спецвент, бортовые отсосы — https://specvent.com/bortovye-otsosy-iz-polipropilena-i-polietilena-dlya-galvanicheskih-vann.html — «Бортовой отсос ПП БО вид 2 - Фу», люки ревизии.
14. Спецвент, ФВГ/ФВА — https://specvent.com/filtr-fva.html
15. Спецвент, вентиляторы — https://specvent.com/ventilyatory.html — ВРП 280-46, ВРП 80-75.
16. SPB Active, воздуховоды из ПП и ПНД — http://spbactive.ru/production/airducts/ — утка, крестовина, врезка, клапаны, компенсатор длины, гибкие вставки, каплеуловители, дефлекторный колпак, зонты вытяжные, цвета ПП и ПНД.
17. SPB Active, утка — http://spbactive.ru/production/airducts/utka/ — определение утки.
18. ПластПлэнт — https://plastplant.ru/plastikovye-vozduhovody/ — «короба», «вентиканалы», «пог. метр».
19. Полимеризделия, сайт — https://izpolimera.ru/vozduhovodi-polipropilen/ — «Шибер (заслонка)/дроссель-клапан/обратный клапан», «Дефлекторные колпаки», «металлические короба», сварка.
20. Полимеризделия, PDF-каталог — https://izpolimera.ru/upload/katalog.pdf — тройник «с отводом», «Бортотсосы».
21. Тетра — https://prom-emkosti.ru/produktsiya/himstojkie-vozduhovody/vozduhovody-iz-polipropilena/ — ⌀110–2000, «раструб (ниппель)», ПП/ПНД/ПВХ/ПВДФ.
22. POLEX VENT, сайт — https://polex-vent.ru/katalog/vozduhovody-iz-polipropilena — «отводы и полуотводы», «факельные выбросы», длины прямых.
23. POLEX VENT, PDF — https://polex-vent.ru/uploads/promotional/file/2/Ventilyatsiya.pdf — перечень фасонных изделий, толщина 3–10 мм.
24. Ватер Групп — https://water-group.ru/katalog/vozduhovody/pryamougolnye-vozduhovody/ — «прямики».
25. Полиюнион — https://polyunion.ru/ventilyatsionnye-sistemy/vozduhovody-ventiljacija-iz-polipropilena — виды соединений (фланцевое, раструбное-муфтовое, ниппельное), блоксополимер, «спецификация в пог.м».
26. УралАктив, зонты вытяжные — https://uralactiv.ru/ventilyatsiya-polipropilenovaya/vozduhovody-iz-polipropilena/zonty-vytyazhnye/ — местные отсосы, зонты-козырьки.
27. УралАктив, бортовые отсосы — https://uralactiv.ru/ventilyatsiya-polipropilenovaya/elementy-ventilyatsii/bortovye-otsosy/
28. УралАктив, ФВГ-ПП-УА — https://uralactiv.ru/gazoochistnoe-oborudovanie/voloknistye-filtry-fvg/
29. Plast Product, ФВГ — https://plast-product.ru/filtryi-voloknistyie-galvanicheskie/ — расшифровка ФВГ и ФКГ, исполнения корпусов.
30. Plast Product, ВРП — https://plast-product.ru/ventilyatoryi-promyishlennyie/ventilyatory-iz-polipropilena/
31. Plast Product, шкафы, зонты, решётки — https://plast-product.ru/shkaf-zont-rechetki — материалы PP, PPs, PPs EL, PVC, PVDF; вытяжные шкафы из ПП.
32. Plast Product, диффузоры — https://plast-product.ru/promyshlennye-diffuzory-plastikovye
33. Кондор-Эко, ФВГ-Т — https://kondor-eco.ru/product/82-voloknistye-filtry-tipa-fvg-t.html
34. ПластПП, каплеуловитель — https://msk.plastpp.ru/cleaning-system/drop-traps/
35. НПО Нева-Актив, каплеуловители — https://npo-neva-aktiv.ru/kapleuloviteli/

Стальная вентиляция и покупное оборудование:
36. Неватом, утки — https://www.nevatom.ru/catalog/utki/
37. Неватом, тройники — https://www.nevatom.ru/catalog/troyniki/ — «тройников, крестовин, врезок», ниппели.
38. Неватом, гибкие вставки — https://www.nevatom.ru/catalog/gibkie_vstavki_vg_vo_vr_kp_vr_vr/ — «Вставка гибкая ВГ-…», «(компенсаторы)».
39. Неватом, виброизоляторы — https://www.nevatom.ru/catalog/vibroizolyatory_vr/ — ДО и ВР.
40. Неватом, обратные клапаны КО «бабочка» — https://www.nevatom.ru/catalog/klapany_obratnye_ko_babochka/
41. Неватом, радиальные вентиляторы — https://www.nevatom.ru/catalog/radialnye_ventilyatory/filter/design-is-vzryvozashchishchennoe_korrozionnostoykoe_teplostoykoe/apply/ — «входной конфузор».
42. Технократ, ниппель и муфта — https://tehnokrat-omsk.ru/nipel.html
43. Вент-Стайл, полуотвод — https://www.vent-style.ru/goods/ugol-45-poluotvod-f-250-iz-ocinkovannoj-stali — «Полуотвод (угол 45) ф 250», перечень покупных сетевых элементов.
44. Вентстар — https://ventstar.ru/poluotvod-45-f-560-ugol-iz-otsinkovannoj-stali/ — переходы, заглушки, зонт прямоугольный.
45. ВентКом, тройник Y (штаны) — https://ventkom.com/fasonnye-izdeliya-dlya-spiralno-navivnyh-vozduhovodov/trojnik-y-shtany/
46. ТехноВент (vektorvent) — https://vektorvent.ru/articles/flancevoe-soedinenie-vozduhovodov/ — «Врезка седло … 900/300*500».
47. Вента, обозначение вентиляторов — https://venta-nt.ru/catalog/ventilyaciya/promyishlennyie-ventilyatoryi-obschie-svedeniya/oboznachenie-ventilyatorov
48. v-klapan.by, коррозионностойкие вентиляторы (PDF) — https://v-klapan.by/upload/iblock/a2f/venilyatiry_vr.pdf — материалы проточной части: стеклопластик, полипропилен, титан, нержавейка.
49. МаксАэро, КВР — https://www.maxaero.by/katalog-produkcii/sobstvennoe-proizvodstvo/zaslonki-vozdushnye/klapan-vozdushnyy-reguliruyushchiy-tipa-kvr
50. МашПром, КПУ-1М — https://www.mashprom.org/ventilyacyonnoe_oborudovanie/klapan_protivopozharnyj_kpu_1_kpu_2_kpu_3/
51. Панорама, противопожарные клапаны (КЛОП с Belimo) — https://panoramavent.ru/product/protivopozharnye-klapany/ognezaderzhivayushhie-klapany/klapan-ognezaderzhivayushhij-kom-1-dlya-protivodymnoj-ventilyacii/ — страница отдаёт раздел КЛОП/КЛАД. Про КОМ-1 — только заголовок в выдаче поиска (не проверено).
52. Belimo LM24A — https://blm.spb.ru/product/lm24a/ — «Привод воздушной заслонки».
53. РОВЕН, ирисовые клапаны — https://rowen.ru/catalog/ventilyatsionnye_klapany/klapany_irisovye/
54. Интеркон, глушители ГТК/ГТП/ГП (серия 5.904-17) — http://intercon.com.ua/wp-content/uploads/2019/06/GTK-GTP-GP-min.pdf
55. Виавент, виброизоляторы — https://viavent.ru/products/vozd/vibroizolyatory/ — ВР 201–203, ДО-38/39.
56. Аэрдин, гибкие вставки — https://aerdyn.ru/gibkie-vstavki/ — ВГК, ВГС, ВГП.
57. СибВентКомплекс, гибкие вставки «В» и «Н» — http://www.sibvent.kz/node/49
58. Градвент, гибкая вставка — https://gradvent.com/komplektuyushchie/gibkaya-vstavka — «вибровставка», «компенсатор».
59. GREMIR, фланцы под бурт — https://gremir.ru/flantsy/flantsy-pod-burt-pod-pe-vtulku/
60. Valfex, бурт ПП под фланец — https://valfex.ru/catalog/polipropilenovye-fitingi-seriya-standard/burt-polipropilenovyy-pod-flanets/

Нормы, стандарты, форумы:
61. ГОСТ 21.602-2016 (PDF) — https://www.eng-in.ru/images/spravka/normativ/GOST-21.602-2016.pdf — марки систем (табл. 1) и элементов (табл. 2), обозначения ⌀, DN, «⌀76х3», порядок «ширина х высота».
62. ГОСТ 21.110-2013 (PDF) — https://stv39.ru/upload/pdf/%D0%A1%D1%82%D1%80%D0%BE%D0%B8%D1%82%D0%B5%D0%BB%D1%8C%D0%BD%D0%BE%D0%B5%20%D0%BE%D0%B1%D0%BE%D1%80%D1%83%D0%B4%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5,%20%D0%BE%D1%81%D0%BD%D0%B0%D1%81%D1%82%D0%BA%D0%B0%20%D0%B8%20%D0%BC%D0%B0%D1%82%D0%B5%D1%80%D0%B8%D0%B0%D0%BB%D1%8B/%D0%A1%D1%82%D1%80%D0%BE%D0%B8%D1%82%D0%B5%D0%BB%D1%8C%D0%BD%D0%BE%D0%B5%20%D0%BE%D0%B1%D0%BE%D1%80%D1%83%D0%B4%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5.pdf — графы спецификации, заголовки разделов, импортное и индивидуальное изготовление.
63. ГОСТ 2.307-2011, раздел 5 (spds.ru) — https://www.spds.ru/info/standarts/2.307-2011/part5.html — знак диаметра (п. 5.38), толщина и длина детали в одной проекции (п. 5.57).
64. ОКЕИ (ОК 015-94) — https://standards.narod.ru/ok/okei.htm — коды 006, 018, 055, 704, 796, 839.
65. РД 95 933-91 «Элементы металлических воздуховодов…» (PDF) — https://files.stroyinf.ru/Data2/1/4293735/4293735461.pdf — типы сечений, углы отводов, коды соединений ФЛ/Б/Р и Ф/С, «бандаж», «тройник штанообразный», «ВхН».
66. Серия 5.904-51 «Зонты и дефлекторы вентиляционных систем» (PDF) — https://files.stroyinf.ru/Data2/2/4294852/4294852971.pdf — назначение зонтов и дефлекторов, детали, таблица До→Д, номера дефлекторов.
67. Серия 1.494-32 (карточка) — https://standartgost.ru/g/%D0%A1%D0%B5%D1%80%D0%B8%D1%8F_1.494-32 — только название. Замена серией 5.904-51 — по выдаче поиска (не проверено).
68. ГОСТ 9639-71 (plastinfo) — https://plastinfo.ru/information/standart/20/445/ — «винипласт листовой».
69. Форум АВОК, «Фасонные элементы воздуховодов в спецификации» — https://forum.abok.ru/lofiversion/index.php/t97255.html — прямики, полуотводы, сегментные отводы, врезки с «сапожками», м² с надбавкой, «Отвод 90 АхВ», «Переход 1 400х400-500х600-800», «хомут+струбцина+шпилька» (форум).

Материалы:
70. Valtec, виды полипропилена — https://valtec.ru/document/article/know_about_polypropilen.html — PP-H, PP-B, PP-R = ПП тип 1/2/3.
71. SIMONA, tech.info PP (PDF, DE) — https://www.simona.de/fileadmin/user_upload/Medien/Mediacenter/Technische_Informationen/tech.info_SIMONA_PP_-deutsch-.pdf — PP-H, PP-C (Block-Copolymer), PPs B1, PP-EL.
72. Энгпласт, ПНД — https://www.engplast.ru/materialy/polietileny-pe/polietilen-nizkogo-davleniya-pend-hdpe/ — ПНД/ПЭНД/HDPE, ПЭ63/80/100 как MRS.
73. Википедия, поливинилиденфторид — https://ru.wikipedia.org/wiki/%D0%9F%D0%BE%D0%BB%D0%B8%D0%B2%D0%B8%D0%BD%D0%B8%D0%BB%D0%B8%D0%B4%D0%B5%D0%BD%D1%84%D1%82%D0%BE%D1%80%D0%B8%D0%B4 — «фторопласт-2».

Зарубежные каталоги:
74. KWERK, Lüftungsformteile (DE) — https://www.kunststoffrohrsysteme.de/lueftungsformteile/index.php?zurueck=1 — Rohrbogen, T-Stück, Hosen T-Stück, Sattelstutzen, Reduzierung, Doppelmuffe, Endboden, Reinigungsöffnung, Drossel-, Absperr-, Regel- и Rückschlagklappe, Deflektorhaube, Regenhaube, Vogelschutzgitter, Wellmanschette, Rohrschalldämpfer, «s=5 mm».
75. SR Kunststofftechnik, Drosselklappen (DE) — https://www.sr-kunststofftechnik.de/drosselklappen.html — PPs, PPs-el, PE-el, PVDF; «da 50 bis da 1.250 mm».
76. SR Kunststofftechnik, Deflektorhaube (DE) — https://www.sr-kunststofftechnik.de/deflektorhaube.html
77. FRANK GmbH, прайс «Flansche, Sonderteile» (PDF, DE/EN) — https://www.frank-gmbh.de/de-wAssets/docs/download-deutsch/download/preislisten/aktuelle_preislisten/17-Preisliste-flansche-sonderteile-komplett.pdf — Losflansch / Backing ring, Vorschweißbund, Bundbuchse, Blindflansch / Blind flange.
78. Simtech AirTech PP (EN, США) — https://www.simtechusa.com/products-and-services/air-handling/at-polypropylene-duct-systems — Elbow, Lateral, Wye, Saddle, Clean-Out, End Cap, Coupling, Reducer, Blind Flange, Back Draft Damper, Deflector, Exhaust Stack, Bird Mesh Grille, Muffler, Expansion Joint, Volume Flow Controller.
79. Asahi/America Pro-Vent (EN) — https://www.asahi-america.com/piping-welding/industrial-piping/pro-vent-duct-system/ — PPs 63–1200 мм, «Back flow dampers», «Tees and wyes».
80. XICHENG EP, PP Ductwork (EN, Китай) — https://air-emissions.com/pps-ducting-and-fittings — butterfly damper, blast gate, backdraft damper, loose-ring flange, PP-C, PPs UL 94 V-0.

### Что найти не удалось (не проверено)
- Названия «звено», «сектор», «обвод», «редукция», «переходник», «адаптер», «торцевая крышка», «пробка», «донышко», «бортовое кольцо», «отбортовка» (как синоним бурта), «мягкая вставка», «гибкий патрубок» как названия изделий в каталогах вентиляции.
- «Дефлектор ЦАГИ» — в загруженных документах нет (серия 5.904-51 называет изделие просто «дефлектор»).
- «Гибкая вставка ВВ» — не найдена. Найдены ВГ, ВГК, ВГС, ВГП, «В» и «Н», «вибровставка».
- Исполнения вентиляторов К1, Ж2, В и клапан КОМ-1 — только по выдаче поиска.
- «шина 20» как обозначение фланца для «фланец20» — не проверено: лимит веб-поиска сессии исчерпан. Вопрос Q40 остаётся открытым.
- Реальную открытую проектную спецификацию раздела ОВ с ПП-воздуховодами найти не удалось. Практика записи взята из каталогов производителей, форума АВОК и строк клиентов из задания.
