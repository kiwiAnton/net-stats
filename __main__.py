from pydantic import BaseModel
import asyncio
import aiohttp
import collections
import matplotlib.pyplot as plt
import json

DO_FETCH = False
BINS = [0, 5000, 10_000, 20_000, 30_000, 40_000]
CUTOFF = 10_000


with open("books.txt") as f:
    text = f.read()

book_name_to_chapters = {}

for line in text.splitlines():
    if not line or line.startswith("("):
        continue
        
    name, chapters = line.split(" – ")
    book_name_to_chapters[name] = int(chapters)


class Passage(BaseModel):
    bookname: str
    chapter: int
    verse: int
    text: str


urls = []

for book_name, chapters in book_name_to_chapters.items():
    urls.extend(
        f"https://labs.bible.org/api/?passage={book_name}+{chapter}&type=json"
        for chapter in range(1, chapters + 1)
    )


async def fetch(url):    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()


async def main():    
    aws = [fetch(url) for url in urls]
    L = await asyncio.gather(*aws)
    return L


if DO_FETCH:
    responses_txt: list[str] = asyncio.run(main())

    with open("responses.txt", "w") as f:
        for response_txt in responses_txt:
            f.write(f"{response_txt}\n")


with open("responses.txt", "r") as f:
    lines = f.readlines()


bible_parts = collections.defaultdict(list)
for line in lines:
    passage_data = eval(line)
    passages = [Passage(**d) for d in passage_data]
    for passage in passages:
        bible_parts[passage.bookname].append(passage.text)


def plot_word_counts():
    bible = {}
    for bookname, parts in bible_parts.items():
        bible[bookname] = "".join(parts)

    bible_words = {bookname: text.split() for bookname, text in bible.items()}
    book_to_word_count = {
        bookname: len(words) for bookname, words in bible_words.items()
    }
    plot_bar(book_to_word_count, "word_count_by_book", sort=False)    
    plot_bar(book_to_word_count, "word_count_by_book_sorted")

    filtered_word_counts = dict(filter(
        lambda kv: kv[1] <= CUTOFF,
        book_to_word_count.items(),
    ))
    plot_bar(
        filtered_word_counts,
        "word_count_by_book_sorted_sub_10000",
    )


    with open("word_count_by_book.json", "w") as f:
        json.dump(book_to_word_count, f, indent=4)    
        
    plot_hist(
        book_to_word_count.values(),
        bins=BINS,
        filename="word_counts_hist",
    )
    
    plot_hist(
        list(book_to_word_count.values()),
        bins=[0, 1000, 2000, 3000, 4000, 5000],
        filename="word_counts_hist_sub_5000",
    )


def plot_bar(book_to_word_count, filename, sort=True):    
    items = book_to_word_count.items()
    if sort:
        items = sorted(items, key=lambda kv: kv[1], reverse=True)

    xs = range(len(items))
    labels = [kv[0] for kv in items]
    ys = [kv[1] for kv in items]

    plt.figure(figsize=[10, 5])
    plt.margins(x=0, y=0, tight=True)
    plt.title(filename)

    plt.bar(xs, ys, align='center')
    plt.xticks(xs, labels=labels, rotation=90)

    plt.grid(which="both", axis="y")

    plt.tight_layout()
    plt.savefig(f"{filename}.png", dpi=150)


def plot_hist(values, bins, filename):
    plt.figure()
    plt.hist(
        values,
        bins=bins,
        edgecolor="black",
        linewidth=1,
    )
    plt.title(filename)
    plt.xticks(bins)
    plt.xlabel("Word count")
    plt.ylabel("Number of books")
    plt.savefig(f"{filename}.png", dpi=150)


plot_word_counts()