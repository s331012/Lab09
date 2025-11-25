import copy

from database.regione_DAO import RegioneDAO
from database.tour_DAO import TourDAO
from database.attrazione_DAO import AttrazioneDAO

class Model:
    def __init__(self):

        self.tour_map = {} # Mappa ID tour -> oggetti Tour
        self.attrazioni_map = {} # Mappa ID attrazione -> oggetti Attrazione
        self.tour_attrazione_map = {}

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0


        # Caricamento
        self.load_tour()
        self.load_attrazioni()
        self.load_relazioni()

    @staticmethod
    def load_regioni():
        """ Restituisce tutte le regioni disponibili """
        return RegioneDAO.get_regioni()

    def load_tour(self):
        """ Carica tutti i tour in un dizionario [id, Tour]"""
        self.tour_map = TourDAO.get_tour()

    def load_attrazioni(self):
        """ Carica tutte le attrazioni in un dizionario [id, Attrazione]"""
        self.attrazioni_map = AttrazioneDAO.get_attrazioni()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra tour e attrazioni e salvarle nelle strutture dati
            Collega tour <-> attrazioni.
            --> Ogni Tour ha un set di Attrazione.
            --> Ogni Attrazione ha un set di Tour.
        """
        tour = {}
        attrazioni = {}

        for item in TourDAO.get_tour_attrazioni():
            tour_id = item["id_tour"]
            attr_id = item["id_attrazione"]

            if tour_id not in tour:
                tour[tour_id] = set()
            tour[tour_id].add(attr_id)

            if attr_id not in attrazioni:
                attrazioni[attr_id] = set()
            attrazioni[attr_id].add(tour_id)

        self.attrazioni_tour = tour
        self.tour_attrazioni = attrazioni

    def genera_pacchetto(self, id_regione: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto turistico ottimale per una regione rispettando i vincoli di durata, budget e attrazioni uniche.
        :param id_regione: id della regione
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Tour)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il valore culturale del pacchetto)
        """
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1

        tour_per_regione = [t for t in self.tour_map.values() if t.id_regione == id_regione]

        self._ricorsione(
            start_index=0,
            tours = tour_per_regione,
            pacchetto_parziale=[],
            durata_corrente= 0,
            costo_corrente=0,
            valore_corrente=0,
            attrazioni_usate=set(),
            max_giorni=max_giorni,
            max_budget=max_budget,
        )

        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, start_index: int, pacchetto_parziale: list, durata_corrente: int, costo_corrente: float, valore_corrente: int, attrazioni_usate: set, tours : list, max_giorni: int = None, max_budget: float = None):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il valore culturale"""

        # TODO: è possibile cambiare i parametri formali della funzione se ritenuto opportuno

        if valore_corrente > self._valore_ottimo:
            self._valore_ottimo = valore_corrente
            self._costo = costo_corrente
            self._pacchetto_ottimo = copy.deepcopy(pacchetto_parziale)

        for i in range(start_index, len(tours)):
            tour = tours[i]

            if max_giorni is not None and durata_corrente + tour.durata_giorni > max_giorni:
                continue
            if max_budget is not None and costo_corrente + tour.costo > max_budget:
                continue

            attr_tour = self.attrazioni_tour.get(tour.id, set())

            if not attr_tour.isdisjoint(attrazioni_usate): #scarta le attrazioni che si ripetono
                continue

            valore_culturale = sum(self.attrazioni_map[att].valore_culturale
                                   for att in attr_tour
                                   if att not in attrazioni_usate)

            pacchetto_parziale.append(tour)

            self._ricorsione(
                start_index= i+1,
                tours= tours,
                pacchetto_parziale= pacchetto_parziale,
                durata_corrente= durata_corrente + tour.durata_giorni,
                costo_corrente= costo_corrente + tour.costo,
                valore_corrente= valore_corrente + valore_culturale,
                attrazioni_usate= attrazioni_usate | attr_tour,
                max_giorni=max_giorni,
                max_budget=max_budget,
            )

            pacchetto_parziale.pop()