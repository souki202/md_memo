var express = require('express');
var app = express();

app.use(express.static('web'));

var port = 443;
app.listen(port,function(){
    console.log("Expressサーバーがポート%dで起動しました。モード:%s",port,app.settings.env)
});