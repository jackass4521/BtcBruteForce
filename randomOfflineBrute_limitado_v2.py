import random
from bit import Key
import multiprocessing
from time import sleep, time
import os

class RandomAddressBrute:
    def __init__(self):
        self.found_file = "foundkey.txt"
        self.start_time = time()
        self.waiting_time = multiprocessing.Manager().dict()  # Tiempo total de espera por hilo
        self.checked_keys = multiprocessing.Manager().dict()  # Total de claves comprobadas por hilo
        self.rate_limit_counts = multiprocessing.Manager().dict()  # Cuenta de rate limit por minuto por hilo
        # Cargar las direcciones desde el archivo una sola vez
        print("Iniciando la carga de direcciones desde address.txt...")
        load_start_time = time()  # Marca el tiempo de inicio de la carga
        loaded_addresses = open("Bitcoin_addresses_LATEST.txt", "r").readlines()
        loaded_addresses = [x.rstrip() for x in loaded_addresses]
        # Remove invalid wallet addresses
        # loaded_addresses = [x for x in loaded_addresses if x.find('wallet') == -1 and len(x) > 0]

        # Inicializar contador de direcciones válidas
        valid_address_count = 0

        # Filtrar las direcciones y contar cuántas se agregan al set
        filtered_addresses = []
        for x in loaded_addresses:
            if x.find('wallet') == -1 and len(x) > 0:
                filtered_addresses.append(x)
                valid_address_count += 1

        # Cargar las direcciones filtradas al set
        self.loaded_addresses = set(filtered_addresses)

        # Imprimir la cantidad de direcciones válidas agregadas al set
        print(f"Se han añadido {valid_address_count} direcciones válidas al conjunto.")

        load_end_time = time()  # Marca el tiempo al final de la carga

        load_duration = load_end_time - load_start_time
        print(f"Direcciones cargadas. Tiempo de carga: {load_duration:.2f} segundos.")

    def display_status(self, num_cores):
        """Muestra una barra de progreso en tiempo real."""
        last_reset = time()
        while True:
            total_checked = sum(self.checked_keys.values())
            total_waiting = sum(self.waiting_time.values())
            total_rate_limits = sum(self.rate_limit_counts.values())
            elapsed_time = time() - self.start_time
            wait_percentage = (total_waiting / elapsed_time * 100) if elapsed_time > 0 else 0

            # Reiniciar el contador de rate limits cada minuto
            if time() - last_reset >= 60:
                for thread_id in self.rate_limit_counts.keys():
                    self.rate_limit_counts[thread_id] = 0
                last_reset = time()

            print(
                f"\r[INFO] Claves comprobadas: {total_checked} | Espera API: {wait_percentage:.2f}% | "
                f"Rate limits/min: {total_rate_limits} | Tiempo transcurrido: {elapsed_time:.2f}s",
                end="",
            )
            sleep(1)

    def random_address_brute(self, thread_id, address_set):
        """Genera claves privadas aleatorias y verifica si la dirección está en address.txt."""
        print(f"Thread {thread_id}: Iniciando búsqueda...")
        self.checked_keys[thread_id] = 0
        self.waiting_time[thread_id] = 0
        self.rate_limit_counts[thread_id] = 0

        while True:
            key = Key()  # Genera clave privada aleatoria
            if key.address in address_set:
                print(f"Thread {thread_id}: ¡Dirección encontrada! 🎉")
                print(f"Dirección pública: {key.address}")
                print(f"Clave privada: {key.to_wif()}")

                # Guarda la clave privada y la dirección pública en un archivo
                with open(self.found_file, "a") as f:
                    f.write(f"{key.address}\n{key.to_wif()}\n")
            else:
                self.checked_keys[thread_id] += 1

    def run(self, num_cores):
        """Ejecuta la búsqueda utilizando múltiples procesos."""
        print(f"Usando {num_cores} núcleos. Iniciando búsqueda...")

        # Iniciar el monitor de progreso
        progress_process = multiprocessing.Process(target=self.display_status, args=(num_cores,))
        progress_process.start()

        # Iniciar procesos manualmente para búsqueda
        jobs = []
        for i in range(num_cores):
            # Pasar la copia del set de direcciones a cada proceso
            p = multiprocessing.Process(target=self.random_address_brute, args=(i, self.loaded_addresses))
            jobs.append(p)
            p.start()

        try:
            for job in jobs:
                job.join()
        except KeyboardInterrupt:
            print("\nBúsqueda detenida por el usuario.")
            for job in jobs:
                job.terminate()
            progress_process.terminate()


if __name__ == "__main__":
    brute = RandomAddressBrute()
    brute.run(4)
