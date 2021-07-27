function burger(x) {
    x.classList.toggle("change");
    document.getElementById('navigation').classList.toggle('small')

    array = document.getElementsByClassName('side-bar-text')
    for (let index = 0; index < array.length; index++) {
        array[index].classList.toggle('hide')

    }

    array = document.getElementsByClassName('icon')
    for (let index = 0; index < array.length; index++) {
        array[index].classList.toggle('hide2')

    }
}

function ChangeTab(tab) {
    var page = [];
    page[0] = "https://app.smartsheet.com/b/form/66aad87216f44c75a9350c7dfccc8b60"
    page[1] = "https://app.smartsheet.com/b/publish?EQBCT=dd419b74d8404d38aba5f1a44043a50a"
    page[2] = "https://app.smartsheet.com/b/publish?EQBCT=139f34614de44ccb8dba8849360b55dc"
    page[3] = "https://app.smartsheet.com/b/publish?EQBCT=b80d157793ea4526b26649c2250f1141"
    page[4] = "https://app.smartsheet.com/b/publish?EQBCT=ec54357ea9ec464b8152bcee18e17c98"
    page[5] = "https://app.smartsheet.com/b/publish?EQBCT=33bbf351a21e4dda836226b392eafeb9"
    page[6] = "https://app.smartsheet.com/b/publish?EQBCT=d6cc3daaf4704185bd309f1ddf80cdf1"
    page[7] = "https://app.smartsheet.com/b/publish?EQBCT=e218fe8635054958ba2b0bd6e0a6a39f"
    page[8] = "https://app.smartsheet.com/b/publish?EQBCT=bf65f74194af4995990be3202a909aea"

    document.getElementById('iframe').src = page[tab]

    if (!document.getElementById('navigation').classList.contains('small')) {
        burger(document.getElementById('burger'))

    }
}
