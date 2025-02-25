# Manual för GS1 Digital Assets System
## Hantering av produktbilder och digitala tillgångar

### Innehållsförteckning
1. Introduktion
2. Mappstruktur
3. Filnamn och format
4. Steg-för-steg guide
5. Checklista
6. Felsökning

### 1. Introduktion
Detta system hanterar dina produktbilder och digitala tillgångar enligt GS1/Validoo standard. 

### 2. Mappstruktur
Varje produkt ska ha en egen mapp som är döpt efter produktens GTIN-nummer.
Exempel: `07309622201028/`

### 3. Filnamn och format
För varje produkt behövs följande filer:

**Produktbild** (obligatorisk)
- Huvudvy (obligatorisk front):
  - Namn: `[GTIN]_C1N1.jpg` eller `product_front.tif`
  - Exempel: `07309622201028_C1N1.jpg`

- Alternativa vyer (valfria):
  - Vänster sida: `[GTIN]_C2N1.jpg`
  - Höger sida: `[GTIN]_C3N1.jpg`
  - Baksida: `[GTIN]_C4N1.jpg`
  - Ovansida: `[GTIN]_C5N1.jpg`
  - Undersida: `[GTIN]_C6N1.jpg`
  - Perspektiv: `[GTIN]_C7N1.jpg`
  - Detalj/närbild: `[GTIN]_C8N1.jpg`
  - Innehåll/förpackning öppen: `[GTIN]_C9N1.jpg`

- Format: JPG eller TIFF
- Krav: 
  - Minst 2400 pixlar på en sida
  - RGB färgrymd
  - Banor (paths) för friläggning
  - Vit bakgrund

**Artwork** (obligatorisk)
- Namn: `artwork_[GTIN].pdf`
- Exempel: `artwork_07309622201028.pdf`
- Format: PDF eller AI

**Planogram** (skapas automatiskt)
- Namn: `planogram_[GTIN]_C1N1.png`
- Skapas automatiskt från produktbilden

**Streckkod** (obligatorisk)
- Namn: `barcode_[GTIN].png`
- Exempel: `barcode_07309622201028.png`
- Format: PNG

### 4. Steg-för-steg guide
1. Skapa en ny mapp med GTIN-nummer
2. Lägg in produktbild
3. Lägg in artwork
4. Lägg in streckkod
5. Vänta på automatisk bearbetning
6. Kontrollera status i webbgränssnittet
7. Godkänn när allt är klart

### 5. Checklista
□ Mapp skapad med korrekt GTIN
□ Produktbild tillagd med rätt namn och format
□ Artwork tillagd med rätt namn
□ Streckkod tillagd
□ Planogram har skapats automatiskt
□ Status visar "Complete" i webbgränssnittet
□ Produkt godkänd

### 6. Felsökning
Vanliga problem och lösningar:
- **Fel filnamn**: Kontrollera att GTIN-nummer är korrekt
- **Bild för liten**: Se till att bilden är minst 2400 pixlar
- **Planogram skapas inte**: Kontrollera att produktbilden har banor
- **Status uppdateras inte**: Uppdatera webbläsaren 