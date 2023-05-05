import logging
import time

from base import Crawler
from settings import CONFIG

logging.basicConfig(format="%(asctime)s %(levelname)s:%(message)s", level=logging.INFO)

crawler = Crawler()

if __name__ == "__main__":
    i = 1
    while True:
        try:
            crawled_page = crawler.crawl_page(
                f"{CONFIG.TINYZONETV_MOVIES_PAGE}?page={i}",
                post_type=CONFIG.TYPE_MOVIE,
            )
            if not crawled_page and i >= CONFIG.TINYZONETV_MOVIES_LAST_PAGE:
                i = 2
            else:
                i += 1
        except Exception as e:
            pass
        time.sleep(CONFIG.WAIT_BETWEEN_ALL)
