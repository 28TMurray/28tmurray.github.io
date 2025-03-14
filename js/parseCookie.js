export function parseCookie() {
    let cookie = new Map()
    if (document.cookie === '') {
        return cookie
    }
    let pairs = document.cookie.split(';')
    for (let pair of pairs) {
        let pairSplit = pair.split('=')
        let key = pairSplit[0].replace(/ /g, '')
        let value = pairSplit[1].replace(/ /g, '')
        cookie.set(key, value)
    }
    return cookie
}

export function getMaxAge(days) {
    return days * 86400 //# of days * seconds in a day
}