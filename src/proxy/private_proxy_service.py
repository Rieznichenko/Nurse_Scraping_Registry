import logging
import random
import traceback
from dataclasses import dataclass
from typing import List, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class Proxy:
    host: str
    port: int
    user: str
    password: str


class PrivateProxyService:
    def __init__(self):
        self.api_key = "076173c40f0e8e8933a737c547f0ee4a"
        self.proxy_packages = ["49460", "49765"]
        self.proxies: List[Proxy] = []

    def get_proxy_list(self) -> List[Proxy]:
        proxies = []
        for proxy_package in self.proxy_packages:
            try:
                response = requests.get(
                    f"https://app.privateproxy.me/api/v1/package_subscriptions/{proxy_package}/ips",
                    auth=("api", self.api_key),
                    timeout=10,
                )
                if response.status_code == 200:
                    for proxy in response.text.split("\n"):
                        proxy = proxy.strip()
                        host, port, user, password = proxy.split(":")
                        proxies.append(Proxy(host=host, port=int(port), user=user, password=password))
            except requests.exceptions.Timeout:
                logger.info("Proxy Service Not Work.")
            except Exception:
                traceback.print_exc()

        logger.info(f"[PROXY] Got {len(proxies)} Proxies.")
        return proxies

    # choose proxy
    def choose_proxy(self) -> Optional[Proxy]:
        if not self.proxies:
            logger.info("[PROXY] Refreshing Proxy List...")
            self.proxies = self.get_proxy_list()
        try:
            proxy = random.choice(self.proxies)
            logger.info(f"[PROXY] Selected Proxy: {proxy} / Remained: {len(self.proxies)}")
            # if self.check_proxy(proxy):
            return proxy
        except IndexError:
            pass

    @staticmethod
    def check_proxy(proxy: Proxy):
        try:
            proxies = {
                "http": f"http://{proxy.user}:{proxy.password}@{proxy.host}:{proxy.port}",
                "https": f"http://{proxy.user}:{proxy.password}@{proxy.host}:{proxy.port}",
            }
            requests.get("http://api.privateproxy.me:10738", proxies=proxies, timeout=10)
            return True
        except Exception:
            traceback.print_exc()
            return False
