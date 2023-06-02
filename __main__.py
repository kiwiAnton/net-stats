from pydantic import BaseModel
import asyncio
import aiohttp
import collections

DO_FETCH = False


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


bible = {}
for bookname, parts in bible_parts.items():
    bible[bookname] = "".join(parts)

print(bible["John"])