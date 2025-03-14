const randomizerProject = document.getElementById("randomizer")
const tierlistProject = document.getElementById("tierlist")
const anyboardProject = document.getElementById("anyboard")

console.log(getFileContent('programming-projects/randomizer.py'))

async function getFileContent(url) {
    return await fetch(url).then((res) => res.text()).then().catch((e) => console.error(e));
}