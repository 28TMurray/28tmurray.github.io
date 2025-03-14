import { parseCookie, getMaxAge } from "./parseCookie.js"

let cookie = parseCookie()
let styleMode = cookie.get('styleMode')
let darkLink = document.getElementById("dark")
let modeToggleButton = document.getElementById("modeToggleButton")
let modeToggleIcon = document.getElementById("modeToggleIcon")
let navLinks = document.getElementsByClassName("navLink")

if (styleMode == 'light') {
    darkLink.setAttribute('href', '')
    modeToggleIcon.setAttribute('src', 'img/moon.svg')
}
else if (styleMode == 'dark'){
    darkLink.setAttribute('href', 'css/dark.css')
    modeToggleIcon.setAttribute('src', 'img/sun.svg')
}
else {
    document.cookie = `styleMode=light; max-age=${getMaxAge(90)}`
    styleMode = 'light'
}

for (let link of navLinks) {
    let fileName = getFileName(link.href)
    let currentFileName = getFileName(window.location.pathname)
    if (currentFileName === fileName) {
        link.style.backgroundColor = '#7cc'
    }
}

function toggleTheme() {
    if (styleMode == 'light') {
        document.cookie = `styleMode=dark; max-age=${getMaxAge(90)}`
    }
    else if (styleMode == 'dark') {
        document.cookie = `styleMode=light; max-age=${getMaxAge(90)}`
    }
    location.reload()
}
modeToggleButton.addEventListener("click", toggleTheme)

function getFileName(path) {
    let fileName = path.substring(path.lastIndexOf('/') + 1)
    return fileName
}