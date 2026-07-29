import { getRoutesForStop, loadGtfs, doesRouteConnect } from './src/services/gtfsService';
import { ensureGtfsData } from './src/utils/gtfsDownloader';
import { PolesService } from './src/services/polesService';

async function run() {
    await ensureGtfsData();
    loadGtfs();
    
    const polesService = new PolesService();
    // Esempio: test direzionalità da Roma Tiburtina (f000014) a Tivoli (f00005)
    const originStopCode = 'f000014';
    const arrivalStopCode = 'f00005';
    
    const polesA = await polesService.getPolesByStopCode(originStopCode);
    const polesB = await polesService.getPolesByStopCode(arrivalStopCode);
    
    const destinationPoleCodes = polesB.map(p => String(p.codicePalina)).filter(Boolean);
    const originPoleCodes = polesA.map(p => String(p.codicePalina)).filter(Boolean);

    const routesA = polesA.flatMap(p => getRoutesForStop(String(p.codicePalina)));
    
    let allowedRouteNames = new Set<string>();
    for (const r of routesA) {
        if (doesRouteConnect(r.routeId, originPoleCodes, destinationPoleCodes)) {
            if (r.routeShortName) allowedRouteNames.add(String(r.routeShortName).toLowerCase());
        }
    }
    
    console.log(`Rotta valida da ${originStopCode} a ${arrivalStopCode}:`, [...allowedRouteNames]);
}

run().catch(console.error);
