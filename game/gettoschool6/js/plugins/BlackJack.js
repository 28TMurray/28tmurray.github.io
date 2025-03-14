//=============================================================================
// BlackJack.js
//=============================================================================
/*:
 * @target MZ
 * @plugindesc Some simple commands for the game of blackjack
 * @author TMurray
 * 
 * @param playerCardsIndex
 * @type number
 * @text Player Cards Variable Index
 * @desc Index of the variable holding the player's cards
 *
 * @param playerCardsValueIndex
 * @type number
 * @text Player Cards Value Variable Index
 * @desc Index of the variable holding the player cards' value
 * 
 * @param dealerCardsIndex
 * @type number
 * @text Dealer Cards Variable Index
 * @desc Index of the variable holding the dealer's cards
 *
 * @param dealerCardsValueIndex
 * @type number
 * @text Dealer Cards Value Variable Index
 * @desc Index of the variable holding the dealer cards' value
 * 
 * @command shuffleDeck
 * @text Shuffle Deck
 * @desc Creates a new deck and shuffles it
 * 
 * @command drawPlayerCard
 * @text Draw Player Cards
 * @desc Draws cards for the player and adds its value to the totals
 * 
 * @arg  amount
 * @type number
 * @text Amount
 * @desc number of cards to draw
 * @default 1
 * 
 * @command drawDealerCard
 * @text Draw Dealer Cards
 * @desc Draws cards for the dealer and adds its value to the totals
 * 
 * @arg  amount
 * @type number
 * @text Amount
 * @desc number of cards to draw
 * @default 1
 * 
*/

(() => {
    const pluginName = "BlackJack";

    const param = PluginManager.parameters(pluginName);

    var defaultDeck = createDefaultDeck();

    var shuffledDeck = shuffle([...defaultDeck]);

    var playerHand = [];

    var dealerHand = [];

    PluginManager.registerCommand(pluginName, "drawPlayerCard", function(args) {
        drawCard(playerHand, param.playerCardsIndex, param.playerCardsValueIndex, args.amount, shuffledDeck);
    });

    PluginManager.registerCommand(pluginName, "drawDealerCard", function(args) {
        drawCard(dealerHand, param.dealerCardsIndex, param.dealerCardsValueIndex, args.amount, shuffledDeck);
    });

    PluginManager.registerCommand(pluginName, "shuffleDeck", function(args) {
        playerHand = [];
        dealerHand = [];
        
        $gameVariables.setValue(param.playerCardsIndex, []);
        $gameVariables.setValue(param.playerCardsValueIndex, 0);
        $gameVariables.setValue(param.dealerCardsIndex, []);
        $gameVariables.setValue(param.dealerCardsValueIndex, 0);

        shuffledDeck = shuffle([...defaultDeck]);
    });

})();

function drawCard(cards, cardsIndex, valueIndex, amount, deck) {

    for (let i = 0; i < amount; i++) {
        cards.push(deck.pop());
    }

    var cardStrings = [];

    var values = [];
        
    var currentValue = $gameVariables.value(valueIndex);
    
    for (let card of cards) {
        let newValue = 0;
        cardStrings.push(card["face"] + card["suit"])
    
        newValue = Number(card["value"]);
        if (card["face"] == "A") {
            if (currentValue + 11 > 21) {
                newValue = card["value"][0];
            }
            else {
                newValue = card["value"][1];
            }
        }
        values.push(newValue);
    }

    console.log(valueIndex, values);
    $gameVariables.setValue(cardsIndex, cardStrings);
    $gameVariables.setValue(valueIndex, values.reduce((partialSum, a) => partialSum + a, 0));
}

function createDefaultDeck() {
    var deckArray = [];
    var suits = ["♠", "♥", "♦", "♣"];
    for (var suit = 0; suit < suits.length; suit++) {
        deckArray.push({"face": "A", "suit" : suits[suit], "value" : [1, 11]});
        
        for (cardNumber = 2; cardNumber <= 10; cardNumber++) {
            deckArray.push({"face": cardNumber, "suit" : suits[suit], "value" : cardNumber});
        }

        deckArray.push({"face" : "J", "suit" : suits[suit], "value" : 10});
        deckArray.push({"face" : "Q", "suit" : suits[suit], "value" : 10});
        deckArray.push({"face" : "K", "suit" : suits[suit], "value" : 10});

    }

    return deckArray;
}

// function taken from this SO answer https://stackoverflow.com/a/12646864
function shuffle(array) {
    for (var i = array.length - 1; i >= 0; i--) {
        var j = Math.floor(Math.random() * (i + 1));
        var temp = array[i];
        array[i] = array[j];
        array[j] = temp;
    }

    return array
}

function sum(array) {
    return [...array] + 0;
}