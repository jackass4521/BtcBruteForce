import requests
from bit import Key
import multiprocessing
from time import sleep, time

class RandomOnlineBrute:
    def __init__(self, found_file="foundkey.txt"):
        self.found_file = found_file
        self.start_time = time()

    def display_status(self, checked_keys, waiting_time, rate_limit_counts, num_cores):
        """Muestra una barra de progreso en tiempo real."""
        while True:
            total_checked = sum(checked_keys)
            total_waiting = sum(waiting_time)
            total_rate_limits = sum(rate_limit_counts)
            elapsed_time = time() - self.start_time
            wait_percentage = (total_waiting / elapsed_time * 100) if elapsed_time > 0 else 0

            print(
                f"\r[INFO] Claves comprobadas: {total_checked} | Espera API: {wait_percentage:.2f}% | "
                f"Rate limits/min: {total_rate_limits} | Tiempo transcurrido: {elapsed_time:.2f}s",
                end="",
            )
            sleep(1)

    def random_online_brute(self, thread_id, checked_keys, waiting_time, rate_limit_counts):
        """Genera claves privadas aleatorias y verifica balances online."""
        print(f"Thread {thread_id}: Iniciando búsqueda...")
        while True:
            key = Key()  # Genera clave privada aleatoria
            try:
                response = requests.get(f"https://blockchain.info/q/getreceivedbyaddress/{key.address}/")
                if response.status_code == 429:  # Rate limiting
                    rate_limit_counts[thread_id] += 1
                    sleep(5)  # Espera 5 segundos antes de continuar
                elif response.status_code == 200:
                    balance = int(response.text)
                    if balance > 0:
                        print(f"Thread {thread_id}: ¡Dirección activa encontrada! 🎉\nDirección: {key.address}\nBalance: {balance}\nClave privada: {key.to_wif()}")
                        with open(self.found_file, "a") as f:
                            f.write(f"{key.address}\n{key.to_wif()}\n")
                    else:
                        checked_keys[thread_id] += 1
            except requests.exceptions.RequestException as e:
                print(f"Thread {thread_id}: Error en la solicitud: {e}  🎉\nDirección: {key.address}\nClave privada: {key.to_wif()}")

    def run(self, num_cores=4):
        """Ejecuta la búsqueda utilizando múltiples procesos."""
        print(f"Usando {num_cores} núcleos. Iniciando búsqueda...")

        # Variables compartidas por los procesos
        checked_keys = multiprocessing.Array('i', [0] * num_cores)  # Contador de claves verificadas
        waiting_time = multiprocessing.Array('d', [0] * num_cores)  # Tiempo de espera por hilo
        rate_limit_counts = multiprocessing.Array('i', [0] * num_cores)  # Conteo de rate limits por hilo

        # Proceso del monitor de progreso
        progress_process = multiprocessing.Process(
            target=self.display_status, args=(checked_keys, waiting_time, rate_limit_counts, num_cores)
        )

        processes = []

        try:
            progress_process.start()  # Inicia el monitor

            # Crear procesos manualmente
            for i in range(num_cores):
                p = multiprocessing.Process(
                    target=self.random_online_brute,
                    args=(i, checked_keys, waiting_time, rate_limit_counts)
                )
                processes.append(p)
                p.start()

            for p in processes:
                p.join()
        except KeyboardInterrupt:
            print("\nBúsqueda detenida por el usuario.")
        finally:
            for p in processes:
                if p.is_alive():
                    p.terminate()
            if progress_process.is_alive():
                progress_process.terminate()


if __name__ == "__main__":
    brute = RandomOnlineBrute()
    brute.run(num_cores=4)