import click
from main import (
    ZulipClient,
    UnreadMessagesFetcher,
    TopicMessagesFetcher,
    Message,
    CsvMessageSaver,
    TextMessageSaver
)


@click.command()
@click.option('--email', required=True, help='Zulip e-mail uživatele')
@click.option('--api-key', required=True, help='Zulip API klíč')
@click.option('--site', required=True, help='Zulip server URL (např. https://zulip.example.com)')
@click.option('--stream', help='Název kanálu (streamu) – povinné pro načtení dle tématu')
@click.option('--topic', help='Název tématu – povinné pro načtení dle tématu')
@click.option('--unread', is_flag=True, help='Načíst pouze nepřečtené zprávy')
@click.option('--output', type=click.Path(), default="messages.txt", help='Cesta k výstupnímu souboru')
@click.option('--format', type=click.Choice(['txt', 'csv']), default='txt', help='Formát výstupu')
def main(email, api_key, site, stream, topic, unread, output, format):
    """
    Načti zprávy ze serveru Zulip a ulož je do souboru (TXT nebo CSV).
    """
    client = ZulipClient(email=email, api_key=api_key, site=site)

    if unread:
        fetcher = UnreadMessagesFetcher(client)
    elif stream and topic:
        fetcher = TopicMessagesFetcher(client, stream, topic)
    else:
        click.echo("❌ Musíš zadat buď --unread nebo kombinaci --stream a --topic.", err=True)
        raise click.Abort()

    response = fetcher.fetch_messages()
    messages = [Message.from_dict(m) for m in response['messages']]

    if format == 'txt':
        saver = TextMessageSaver(output)
    else:
        saver = CsvMessageSaver(output)

    saver.save_messages(messages)
    click.echo(f"✅ Uloženo {len(messages)} zpráv do souboru: {output}")


if __name__ == '__main__':
    main()
