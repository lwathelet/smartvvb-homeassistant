# SmartVVB voor Home Assistant

*[English](README.md) · [Français](README.fr.md) · Nederlands*

[![Validate](https://github.com/lwathelet/smartvvb-homeassistant/actions/workflows/validate.yml/badge.svg)](https://github.com/lwathelet/smartvvb-homeassistant/actions/workflows/validate.yml)

Bewaak en bedien je [SmartVVB](https://smartvvb.no) boiler vanuit Home Assistant.

Dit is de Home Assistant-tegenhanger van de SmartVVB Homey-app: dezelfde backend, dezelfde functies.

## Functies

**Boiler** (één per apparaat):
- Huidige watertemperatuur en het setpoint van de potentiometer op de boiler (alleen-lezen)
- Bedrijfsmodus en afwezigheidsmodus

**Sensoren:**
- Watertemperatuur, huidig vermogen, energieverbruik vandaag, kosten vandaag (NOK)
- Beschikbaar warm water en waterverbruik vandaag, in liter
- WiFi-signaalsterkte (standaard uitgeschakeld, in te schakelen bij de entiteitsinstellingen)

"Energie vandaag" kan aan het **Energie-dashboard** van Home Assistant worden toegevoegd.

**Binaire sensoren:**
- Verwarmen: aan zolang de boiler vermogen opneemt
- Waterveiligheid: Veilig / Onveilig (legionella-indicator)

**Bedienen:**
- Modusselectie: Off, Away, Economy, Standard, Comfort, Auto, Always on
- Knoppen Forceer aan / Forceer uit (tijdelijke override van 2 uur, zie opmerking hieronder)
- Maximale energie per uur (standaard uitgeschakeld, in te schakelen bij de entiteitsinstellingen)

**Actie `smartvvb.set_max_energy_schedule`:** stelt voor elk van de 24 uren van de dag een maximaal vermogen (W) in, waarbij 0 een uur blokkeert. Handig met een integratie voor stroomprijzen om dure uren te vermijden:

```yaml
action: smartvvb.set_max_energy_schedule
data:
  device_id: <je SmartVVB-apparaat>
  hours: [2000, 2000, 2000, 2000, 2000, 2000, 0, 0, 0, 2000, 2000, 2000,
          2000, 2000, 2000, 2000, 0, 0, 0, 0, 2000, 2000, 2000, 2000]
```

**Diagnostiek:** apparaatpagina → ⋮ → Diagnostiek downloaden (inloggegevens worden verwijderd).

**Updates:** elke minuut opgehaald uit de SmartVVB-cloud (de backend slaat één meting per minuut op). Er is geen webhook of externe toegang tot Home Assistant nodig.

## Belangrijk: Forceer aan/uit is een override van 2 uur, geen schakelaar

Het `/ForceDevice`-eindpunt van de backend is gedocumenteerd als "force device for 2 hours". Het is een tijdelijke override bovenop de actieve modus, geen permanente aan/uit-status. Daarom wordt dit in deze integratie weergegeven als twee **knoppen**, niet als een `switch`-entiteit: een schakelaar veronderstelt een stabiele, afleesbare status, en dat is hier niet het geval.

## Installatie

### HACS (aanbevolen)

[![Open je Home Assistant-instantie en deze repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=lwathelet&repository=smartvvb-homeassistant&category=integration)

Of handmatig in HACS:
1. HACS → ⋮ → Aangepaste repositories → voeg `https://github.com/lwathelet/smartvvb-homeassistant` toe, type "Integratie".
2. Zoek "SmartVVB", download het en herstart Home Assistant.

### Handmatig
Kopieer `custom_components/smartvvb` naar de `custom_components`-map van je Home Assistant en herstart.

## Instellen
Instellingen → Apparaten en diensten → Integratie toevoegen → SmartVVB → voer je SmartVVB-gebruikersnaam en wachtwoord in.

Alleen het verkregen toegangstoken wordt opgeslagen (het token van de backend verloopt niet); je wachtwoord wordt nooit bewaard.

## Meerdere apparaten
Als je account meerdere SmartVVB-apparaten heeft, krijgt elk apparaat na het instellen automatisch zijn eigen set entiteiten. Je hoeft de integratie niet meerdere keren toe te voegen.

## Ondersteuning
Meld problemen via [GitHub issues](https://github.com/lwathelet/smartvvb-homeassistant/issues). Het diagnostiekbestand meesturen helpt.
