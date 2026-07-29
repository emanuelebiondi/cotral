Oggetti principali

- Pole (palina): rappresenta una palina o punto di fermata. Campi:
	- `codicePalina`, `codiceStop`: identificatori.
	- `nomePalina`, `nomeStop`, `localita`, `comune`: etichette testuali.
	- `coordX`, `coordY`: coordinate (numero, lat/lon).
	- `destinazioni`: array di destinazioni raggiungibili dalla palina.
	- flag: `isCotral`, `isCapolinea`, `isBanchinato` (numerici/nullabili).
	- `preferita`: boolean se l'utente l'ha marcata.
	- Provenienza: mappata da GTFS o dall'XML Cotral (vedi `PolesService`).

- Stop (fermata): rappresentazione minima di una fermata GTFS.
	- `codiceStop`, `nomeStop`, `localita`, `coordX`, `coordY`.
	- Usata per ricerche per località, lookup GTFS e per trovare paline vicine.

- Transit (transito): singolo passaggio/occorrenza di una corsa su una palina.
	- Campi principali: `idCorsa`, `percorso`, `orarioPartenzaCorsa`, `orarioArrivoCorsa`, `ritardo`, `passato`, `soppressa`, `numeroOrdine`, `banchina`, `monitorata`, `accessibile`.
	- `automezzo`: oggetto `Vehicle` associato (se disponibile).
	- Derivazione: normalizzato dall'API Cotral in `TransitsService`.

- Vehicle (veicolo): metadati sul mezzo.
	- `codice`: identificatore del veicolo.
	- `isAlive`: boolean che indica se il tracking è attivo.
	- Usato per richiedere le posizioni real‑time.

- VehiclePosition (posizione): traccia/posizioni GPS di un veicolo.
	- `coordX`: array di stringhe (coordinate X/lat come parti di traccia).
	- `coordY`: array di stringhe (coordinate Y/lon).
	- `time`: timestamp o valore temporale associato.

Relazioni e flusso dei dati
- Per una `Pole` si richiedono i `Transit` via `TransitsService.getTransitsByPoleCode`.
- Ogni `Transit` può contenere `automezzo.codice`; con quel codice si richiedono le `VehiclePosition` via `VehiclesService.getVehicleRealTimePositions`.
- GTFS (`gtfsService`) fornisce mapping stop↔route e destinazioni; è usato per trovare paline vicine, ricavare destinazioni, e per euristiche di filtro (es. match route tra stop A e B).

Esempio d'uso (endpoint aggiunto)
- GET `/stops/:stopCode/transits-positions` → restituisce per la fermata indicata l'elenco delle paline vicine, per ogni palina i transiti previsti e, quando disponibile, le posizioni real‑time dei veicoli.
- Query opzionale: `arrivalStopCode` → applica un filtro GTFS per tenere solo i transiti che collegano la fermata di partenza e quella di arrivo (euristica basata su route comuni).

Struttura di risposta tipica:
{
	"stopCode": "12345",
	"arrivalStopCode": "67890" | null,
	"poles": [
		{
			"pole": { /* Pole */ },
			"transits": [
				{
					"transit": { /* Transit */ },
					"vehiclePositions": [ /* array di VehiclePosition */ ]
				}
			]
		}
	]
}

Se vuoi, posso aggiungere esempi reali di payload chiamando l'API con un codice fermata reale, oppure inserire questa documentazione nel README del server.

