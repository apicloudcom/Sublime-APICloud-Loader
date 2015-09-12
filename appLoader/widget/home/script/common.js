var toWeb = function(obj){
    var url = $api.attr(obj,'data-url') ||'';
    var title = $api.attr(obj,'data-title');
    var frameName = $api.attr(obj,'data-frameName');
    var options = {
            title: title,
            url: url,
            frameName: frameName
        };
    options = JSON.stringify(options);
    var str = 'indexToWeb('+options+')';
    api.execScript({
        name: 'root',
        script: str
    });
};
var toNativeSearch = function(obj){
    var title = $api.attr(obj,'data-title');
    var pageParam = {
            title: title
        };
    pageParam = JSON.stringify(pageParam);
    var str = 'indexToNativeSearch('+pageParam+')';
    api.execScript({
        name: 'root',
        script: str
    });
    
};