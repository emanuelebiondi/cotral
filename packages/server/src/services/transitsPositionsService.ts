import { PolesService } from './polesService';
import { TransitsService } from './transitsService';
import { VehiclesService } from './vehiclesService';
import * as gtfs from './gtfsService';

export class TransitsPositionsService {
    private polesService: PolesService;
    private transitsService: TransitsService;
    private vehiclesService: VehiclesService;

    constructor() {
        this.polesService = new PolesService();
        this.transitsService = new TransitsService();
        this.vehiclesService = new VehiclesService();
    }

    /**
     * Returns poles for a stop and their transits with real-time vehicle positions.
     * If arrivalStopCode is provided, transits are filtered to those whose route
     * matches routes serving both stops (GTFS-based heuristic).
     */
    public async getTransitsAndPositionsByStop(stopCode: string, arrivalStopCode?: string) {
        const poles = await this.polesService.getPolesByStopCode(stopCode);

        // Build a set of allowed route identifiers (short/long names) if arrivalStopCode provided
        let allowedRouteNames: Set<string> | null = null;
        if (arrivalStopCode) {
            const polesB = await this.polesService.getPolesByStopCode(arrivalStopCode);
            const destinationPoleCodes = polesB.map(p => p.codicePalina).filter(Boolean) as string[];
            const originPoleCodes = poles.map(p => p.codicePalina).filter(Boolean) as string[];

            const routesA = poles.flatMap(p => gtfs.getRoutesForStop(String(p.codicePalina)));
            
            allowedRouteNames = new Set<string>();
            for (const r of routesA) {
                if (gtfs.doesRouteConnect(r.routeId, originPoleCodes, destinationPoleCodes)) {
                    if (r.routeShortName) allowedRouteNames.add(String(r.routeShortName).toLowerCase());
                    if (r.routeLongName) allowedRouteNames.add(String(r.routeLongName).toLowerCase());
                }
            }
            // If there are no connecting routes, set allowedRouteNames to empty set (no results)
            if (allowedRouteNames.size === 0) allowedRouteNames = new Set();
        }

        const results = [] as any[];

        for (const pole of poles) {
            const poleCode = pole.codicePalina ?? '';
            if (!poleCode) continue;

            const transitBundle = await this.transitsService.getTransitsByPoleCode(poleCode);
            if (!transitBundle) continue;

            const transits = transitBundle.transits ?? [];

            // Optionally filter by allowed routes derived from GTFS
            const filteredTransits = allowedRouteNames ? transits.filter(t => {
                const percorso = (t.percorso || '').toLowerCase();
                // If allowedRouteNames is empty, nothing matches
                if (allowedRouteNames!.size === 0) return false;
                for (const rn of allowedRouteNames!) {
                    if (!rn) continue;
                    if (percorso.includes(rn)) return true;
                }
                return false;
            }) : transits;

            // For each transit get vehicle positions (in parallel)
            const transitWithPositions = await Promise.all(filteredTransits.map(async (t) => {
                const vehicleCode = t.automezzo?.codice ?? null;
                let positions = [] as any[];
                try {
                    if (vehicleCode) positions = await this.vehiclesService.getVehicleRealTimePositions(String(vehicleCode));
                } catch (e) {
                    // ignore vehicle failures, leave positions empty
                }

                return {
                    transit: t,
                    vehiclePositions: positions
                };
            }));

            results.push({ pole: transitBundle.pole, transits: transitWithPositions });
        }

        return { stopCode, arrivalStopCode: arrivalStopCode ?? null, poles: results };
    }
}
