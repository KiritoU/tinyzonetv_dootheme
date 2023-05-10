import json
import logging
import sys

from bs4 import BeautifulSoup

from dootheme import Dootheme
from helper import helper
from settings import CONFIG

logging.basicConfig(format="%(asctime)s %(levelname)s:%(message)s", level=logging.INFO)


class Crawler:
    def crawl_soup(self, url):
        logging.info(f"Crawling {url}")

        html = helper.download_url(url)
        soup = BeautifulSoup(html.content, "html.parser")

        return soup

    def get_episodes_data(
        self, href: str, soup: BeautifulSoup, post_type: str = CONFIG.TYPE_TV_SHOWS
    ) -> dict:
        res = {}

        try:
            watching_player_area = soup.find("div", class_="watching_player-area")
            res["tmdb_id"] = watching_player_area.get("data-tmdb-id")
            if post_type == CONFIG.TYPE_TV_SHOWS:
                seasons_list = soup.find("div", class_="seasons-list")
                slc_seasons = seasons_list.find("div", class_="slc-seasons")
                lis = slc_seasons.find_all("li")
                for li in lis:
                    a_element = li.find("a")

                    season_title = a_element.get("title")
                    res.setdefault(season_title, {})

                    season_href = a_element.get("href")
                    season_id = season_href.replace("#", "")
                    season_episodes = soup.find("div", {"id": season_id})
                    for episode in season_episodes.find_all("a", class_="episode-item"):
                        episode_number = episode.get("data-number")
                        episode_title = episode.get("title")
                        res[season_title][episode_number] = episode_title

        except Exception as e:
            helper.error_log(
                f"Failed to get_episodes_data. Href: {href}",
                log_file="base.episodes.log",
            )

        return res

    def crawl_film(
        self,
        title: str,
        slug: str,
        fd_infor: list,
        quality: str,
        cover_src: str,
        href: str,
        post_type: str = CONFIG.TYPE_TV_SHOWS,
    ):
        soup = self.crawl_soup(href)
        detail_page_infor = soup.find("div", class_="detail_page-infor")

        title = (
            title
            if title
            else helper.get_title(href=href, detail_page_infor=detail_page_infor)
        )
        description = helper.get_description(
            href=href, detail_page_infor=detail_page_infor
        )

        cover_src = (
            cover_src
            if cover_src
            else helper.get_cover_url(href=href, detail_page_infor=detail_page_infor)
        )

        trailer_id = helper.get_trailer_id(soup)
        extra_info = helper.get_extra_info(detail_page_infor=detail_page_infor)
        extra_info["quality"] = quality

        if not title:
            helper.error_log(
                msg=f"No title was found. Href: {href}", log_file="base.no_title.log"
            )
            return

        film_data = {
            "title": title,
            "slug": slug,
            "description": description,
            "post_type": post_type,
            "trailer_id": trailer_id,
            "cover_src": cover_src,
            "extra_info": extra_info,
        }

        episodes_data = self.get_episodes_data(
            href=href, soup=soup, post_type=post_type
        )

        return film_data, episodes_data

    def crawl_flw_item(
        self, flw_item: BeautifulSoup, post_type: str = CONFIG.TYPE_TV_SHOWS
    ):
        try:
            film_poster = flw_item.find("div", class_="film-poster")
            if film_poster:
                film_poster_quality = film_poster.find(
                    "div", class_="film-poster-quality"
                )
                quality = film_poster_quality.text if film_poster_quality else "HD"

                img = film_poster.find("img")
                cover_src = img.get("data-src") if img else ""

                a_element = film_poster.find("a")
                href = a_element.get("href") if a_element else ""

            film_detail = flw_item.find("div", class_="film-detail")
            if film_detail:
                film_name = film_detail.find("h3", class_="film-name")
                if film_name:
                    if film_name.find("a") and not href:
                        href = film_name.find("a").get("href")
                    title = film_name.text.strip("\n")

                fd_infor = film_detail.find("div", class_="fd-infor")
                fd_infor = fd_infor.text if fd_infor else ""
                fd_infor = [x for x in fd_infor.split("\n") if x]

            if "http" not in href:
                href = CONFIG.TINYZONETV_HOMEPAGE + href

            slug = href.split("/")[-1]

            film_data, episodes_data = self.crawl_film(
                title=title,
                slug=slug,
                fd_infor=fd_infor,
                quality=quality,
                cover_src=cover_src,
                href=href,
                post_type=post_type,
            )

            # film_data["episodes_data"] = episodes_data

            # with open("json/crawled.json", "w") as f:
            #     f.write(json.dumps(film_data, indent=4, ensure_ascii=False))

            Dootheme(film=film_data, episodes=episodes_data).insert_film()
            # sys.exit(0)
        except Exception as e:
            helper.error_log(
                msg=f"Error crawl_flw_item\n{e}", log_file="base.crawl_flw_item.log"
            )

    def crawl_page(self, url, post_type: str = CONFIG.TYPE_TV_SHOWS):
        soup = self.crawl_soup(url)

        film_list_wrap = soup.find("div", class_="film_list-wrap")
        if not film_list_wrap:
            return 0

        flw_items = film_list_wrap.find_all("div", class_="flw-item")
        if not flw_items:
            return 0

        for flw_item in flw_items:
            self.crawl_flw_item(flw_item=flw_item, post_type=post_type)

        return 1

    def update(
        self,
        url: str = CONFIG.TINYZONETV_HOMEPAGE,
    ):
        try:
            soup = self.crawl_soup(url)

            block_area_homes = soup.find_all("section", class_="block_area_home")
            if len(block_area_homes) != 4:
                print("len(block_area_homes) != 4", len(block_area_homes))
                return

            tv_show_flw_items = block_area_homes[-1].find_all("div", class_="flw-item")
            for flw_item in tv_show_flw_items:
                self.crawl_flw_item(flw_item=flw_item, post_type=CONFIG.TYPE_TV_SHOWS)

            tv_show_flw_items = block_area_homes[-2].find_all("div", class_="flw-item")
            for flw_item in tv_show_flw_items:
                self.crawl_flw_item(flw_item=flw_item, post_type=CONFIG.TYPE_MOVIE)

            return
        except Exception as e:
            print(e)


if __name__ == "__main__":
    Crawler().crawl_page(url=CONFIG.TINYZONETV_TVSHOWS_PAGE + "?page=1")
    # Crawler().crawl_page(url=CONFIG.TINYZONETV_MOVIES_PAGE, post_type=CONFIG.TYPE_MOVIE)
