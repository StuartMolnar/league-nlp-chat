const axios = require('axios');
const logger = require('./log_conf');



//todo 

// https://www.op.gg/statistics/champions?hl=en_US
// https://runes.lol/champion/akali/runes/
// go through all champions
// get top rune builds by champion from text

// another services downloads a list of all runes and their descriptions 
// stores that info to a separate database table

// update challenger_stats service to grab rune id data from the matches and get associated rune names from the above database

// last service will get champion statistics i.e. pick rates and win rates and store in another table

// --- work on the rune list with descriptions service first, then update the challenger stats ---