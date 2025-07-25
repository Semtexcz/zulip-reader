import csv
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any
from html import unescape

import arrow
import zulip


class MessageClient(ABC):
    @abstractmethod
    def get_messages(self, parameters: Dict[str, Any]) -> Any:
        pass


class ZulipClient(MessageClient):
    def __init__(self, email: str, api_key: str, site: str):
        self.email = email
        self.api_key = api_key
        self.site = site
        self.client = self._initialize_client()

    def _initialize_client(self):
        # Inicializace skutečného Zulip klienta s použitím emailu, api_key a site
        return zulip.Client(email=self.email, api_key=self.api_key, site=self.site)

    def get_messages(self, parameters: Dict[str, Any]) -> Any:
        return self.client.get_messages(parameters)


class Channel:
    def __init__(
            self,
            stream_id: int,
            name: str,
            description: str,
            rendered_description: str,
            date_created: int,
            creator_id: int = None,
            invite_only: bool = False,
            subscribers: list[int] = None,
            desktop_notifications: bool = None,
            email_notifications: bool = None,
            wildcard_mentions_notify: bool = None,
            push_notifications: bool = None,
            audible_notifications: bool = None,
            pin_to_top: bool = False,
            is_muted: bool = False,
            in_home_view: bool = None,
            is_announcement_only: bool = None,
            is_web_public: bool = False,
            color: str = "",
            stream_post_policy: int = 1,
            message_retention_days: int = None,
            history_public_to_subscribers: bool = True,
            first_message_id: int = None,
            stream_weekly_traffic: int = None,
            can_remove_subscribers_group: int = None,
    ):
        self.stream_id = stream_id
        self.name = name
        self.description = description
        self.rendered_description = rendered_description
        self.date_created = date_created
        self.creator_id = creator_id
        self.invite_only = invite_only
        self.subscribers = subscribers if subscribers is not None else []
        self.desktop_notifications = desktop_notifications
        self.email_notifications = email_notifications
        self.wildcard_mentions_notify = wildcard_mentions_notify
        self.push_notifications = push_notifications
        self.audible_notifications = audible_notifications
        self.pin_to_top = pin_to_top
        self.is_muted = is_muted
        self.in_home_view = in_home_view
        self.is_announcement_only = is_announcement_only
        self.is_web_public = is_web_public
        self.color = color
        self.stream_post_policy = stream_post_policy
        self.message_retention_days = message_retention_days
        self.history_public_to_subscribers = history_public_to_subscribers
        self.first_message_id = first_message_id
        self.stream_weekly_traffic = stream_weekly_traffic
        self.can_remove_subscribers_group = can_remove_subscribers_group

    def __repr__(self):
        return f"<Channel {self.name} (ID: {self.stream_id})>"


class ChannelFetcher(ABC):
    def __init__(self, zulip_client):
        self._zulip_client = zulip_client

    @property
    def zulip_client(self):
        return self._zulip_client

    @abstractmethod
    def fetch_channels(self):
        pass


class SubscribedChannelsFetcher(ChannelFetcher):
    def fetch_channels(self) -> List[Channel]:
        channels: Dict[str, Any] = self.zulip_client.get_subscriptions()
        return [Channel(**channel) for channel in channels['subscriptions']]


class AllChannelsFetcher(ChannelFetcher):
    def fetch_channels(self) -> List[Channel]:
        channels: Dict[str, Any] = self.zulip_client.get_streams()
        return [Channel(**channel) for channel in channels['streams']]


class Anchor(Enum):
    NEWEST = "newest"
    FIRST_UNREAD = "first_unread"
    OLDEST = "oldest"


# Konfigurace pro získávání zpráv
class MessageFetcherConfig:
    def __init__(self, narrow: List | None = None, anchor: Anchor | int = Anchor.NEWEST, num_before: int = 100,
                 num_after: int = 0):
        self.narrow = narrow if narrow is not None else []
        self.anchor = anchor
        self.num_before = num_before
        self.num_after = num_after

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anchor": self.anchor.value,
            "num_before": self.num_before,
            "num_after": self.num_after,
            "narrow": self.narrow
        }


class MessageFetcher(ABC):
    def __init__(self, message_client: MessageClient, config: MessageFetcherConfig):
        self._message_client = message_client
        self._config = config

    def get_messages(self):
        return self._message_client.get_messages(self._config.to_dict())

    @property
    def message_client(self) -> MessageClient:
        return self._message_client

    @abstractmethod
    def fetch_messages(self):
        pass


class UnreadMessagesFetcher(MessageFetcher):
    def __init__(self, message_client: MessageClient):
        # Konfigurace narrow, která zahrnuje pouze nepřečtené zprávy
        unread_narrow = [{"operator": "is", "operand": "unread"}]
        config = MessageFetcherConfig(
            narrow=unread_narrow,  # [],
            anchor=Anchor.NEWEST,
            num_before=5000,
            num_after=0
        )
        super().__init__(message_client, config)

    def fetch_messages(self):
        return self.get_messages()


class TopicMessagesFetcher(MessageFetcher):
    def __init__(self, message_client: MessageClient, stream_name: str, topic_name: str):
        # Konfigurace narrow, která zahrnuje pouze nepřečtené zprávy
        narrow = [
            {"operator": "stream", "operand": stream_name},  # Název kanálu
            {"operator": "topic", "operand": topic_name}  # Název tématu
        ]

        config = MessageFetcherConfig(
            narrow=narrow,  # [],
            anchor=Anchor.NEWEST,
            num_before=5000,
            num_after=0
        )
        super().__init__(message_client, config)

    def fetch_messages(self):
        return self.get_messages()


@dataclass
class Message:
    id: int
    datetime: arrow.Arrow
    display_recipient: str
    subject: str
    sender_full_name: str
    content: str

    @staticmethod
    def from_dict(message_dict: Dict[str, Any]) -> 'Message':
        return Message(
            id=message_dict['id'],
            datetime=arrow.get(message_dict['timestamp']),
            display_recipient=message_dict['display_recipient'],
            subject=message_dict['subject'],
            sender_full_name=message_dict['sender_full_name'],
            content=message_dict['content']
        )


class MessageSaver(ABC):
    @abstractmethod
    def save_messages(self, messages: List[Message]):
        pass


class CsvMessageSaver(MessageSaver):
    def __init__(self, filename: str):
        self.filename = filename

    def save_messages(self, messages: List[Message]):
        with open(self.filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            # Zápis hlavičky CSV
            writer.writerow(['ID', 'Date', 'Channel', 'Topic', 'Author', 'Content'])

            for message in messages:
                # Konverze timestampu na ISO formát pomocí arrow
                iso_date = message.datetime.isoformat()

                # Zápis řádku do CSV
                writer.writerow(
                    [message.id, iso_date, message.display_recipient, message.subject, message.sender_full_name,
                     message.content])


class TextMessageSaver(MessageSaver):
    def __init__(self, filename: str):
        self.filename = filename

    def save_messages(self, messages: List[Message]):
        # Seřazení zpráv podle timestampu (datetime)
        sorted_messages = sorted(messages, key=lambda msg: msg.datetime)

        with open(self.filename, mode='w', encoding='utf-8') as file:
            for message in sorted_messages:
                # Konverze timestampu na ISO formát pomocí arrow
                iso_date = message.datetime.isoformat()

                # Odstranění HTML značek z obsahu zprávy
                clean_content = self._remove_html_tags(message.content)

                # Zápis zprávy do textového souboru
                file.write(f'ID: {message.id}\n')
                file.write(f'Date: {iso_date}\n')
                file.write(f'Channel: {message.display_recipient}\n')
                file.write(f'Topic: {message.subject}\n')
                file.write(f'Author: {message.sender_full_name}\n')
                file.write(f'Content:\n{clean_content}\n')
                file.write('\n' + '-' * 40 + '\n\n')

    def _remove_html_tags(self, text: str) -> str:
        # Odstranění HTML značek pomocí regulárních výrazů
        clean_text = re.sub(r'<[^>]+>', '', text)
        return unescape(clean_text)
