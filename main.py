from http import HTTPStatus
from http.client import HTTPConnection, HTTPSConnection
from sys import argv
from time import perf_counter_ns
from urllib.parse import urlparse



def test_download(url: str) -> tuple[int, float]:
    parsed_url = urlparse(url)

    if parsed_url.scheme not in ('http', 'https'):
        raise ValueError('Invalid protocol')

    conn_cls = HTTPConnection if parsed_url.scheme == 'http' else HTTPSConnection

    conn = conn_cls(parsed_url.netloc, timeout=30)

    path = parsed_url.path or '/'
    if parsed_url.query:
        path += '?' + parsed_url.query

    try:
        conn.request('GET', path)

        response = conn.getresponse()
        if response.status != HTTPStatus.OK:
            raise RuntimeError(f'HTTP {response.status}: {response.reason}')

        total_bytes = 0
        start = perf_counter_ns()

        while chunk := response.read(8196):
            total_bytes += len(chunk)

        elapsed = (perf_counter_ns() - start) / 1_000_000_000

        return total_bytes, elapsed

    finally:
        conn.close()


def get_speed_mb_string(bytes_downloaded: int,
                        seconds_elapsed: int | float,
                        prec: int = 2) -> str:
    speed = bytes_downloaded / (seconds_elapsed * (1 << 20))
    return f'{speed:.{prec}f} MB/s'


def print_single_test_result(bytes_downloaded: int,
                             seconds_elapsed: float,
                             test_number: int) -> None:
    speed_str = get_speed_mb_string(bytes_downloaded=bytes_downloaded,
                                    seconds_elapsed=seconds_elapsed)
    print(
        f'Test {test_number}: '
        f'{bytes_downloaded} bytes downloaded, '
        f'time: {seconds_elapsed:.2f} seconds, '
        f'speed: {speed_str}'
    )


def main(n: int = 10):
    args = argv[1:]
    if not args:
        raise ValueError('File url not specified')
    url = args[0]

    total_downloaded = 0
    total_seconds_elapsed = 0

    for i in range(1, n + 1):
        bytes_downloaded, seconds_elapsed = test_download(url)
        print_single_test_result(bytes_downloaded=bytes_downloaded,
                                 seconds_elapsed=seconds_elapsed,
                                 test_number=i)
        total_downloaded += bytes_downloaded
        total_seconds_elapsed += seconds_elapsed

    avg_speed_str = get_speed_mb_string(bytes_downloaded=total_downloaded,
                                        seconds_elapsed=total_seconds_elapsed)

    print(
        'Done. '
        f'Total bytes downloaded: {total_downloaded}, '
        f'time: {total_seconds_elapsed:.2f} seconds, '
        f'average speed: {avg_speed_str}'
    )


if __name__ == "__main__":
    main()
