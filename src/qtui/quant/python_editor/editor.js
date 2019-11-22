//////////////////////////////////////////////////////////////////////////////
// 文件名：editor.js
// 作者：  刘明祥
// 功能：  实现VScode中的代码编辑器调用, 在网页中嵌入monaco.editor，并在本地进程中嵌入一个浏览器打开该网页
//        在网页中创建websocket客户端和同一本地进程里的websocket服务端通信来完成代码文件的加载与保存
//
// JSON格式的协议：
// 设置主题
// {"cmd":"settheme", theme":"", "fontsize":12}
// 打开文件
// {"cmd":"openfile", "file":"", "txt":""}
// 保存文件
// {"cmd":"savefile_req", "reqid":0, "file":""}
// {"cmd":"savefile_rsp", "reqid":0, "file":"", "txt":"", "errtxt":""}
// 文件修改通知
// {"cmd":"modify_nty", "file":""}
//////////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////////////
///websocket客户端通道
//////////////////////////////////////////////////////////////////////////////
new QWebChannel(qt.webChannelTransport,
    function (channel) {
        window.Bridge = channel.objects.Bridge;

        // 绑定自定义的信号customSignal
        Bridge.customSignal.connect(function (file, text) {
            add_tab(file, text);
        });
        Bridge.saveSignal.connect(function (file){
            save_file(file, false)
        });
        Bridge.setThemeSignal.connect(function (text) {
            set_theme(text, '');
            if (text == 'vs-dark'){
                document.getElementById('main_link').href = 'editor.css'
            }else {
                document.getElementById('main_link').href = 'editor_vs.css'
            }
        });
    }
);

//////////////////////////////////////////////////////////////////////////////
///代码编辑器 monaco.editor
//////////////////////////////////////////////////////////////////////////////

//当前代码编辑器所打开的文件，为空则为新建文件
var g_model = null;
var g_filename = "";
//编辑器实例
var g_editor = null;

//屏蔽右键
document.oncontextmenu=new Function("event.returnValue=false;");

//初始化编辑器
function init_editor(layoutid, code_str, theme) {
    if (g_editor)
        return;
    //初始化编辑器
    require.config(
        {
            paths: {'vs': 'monaco-editor/package/min/vs'},
            'vs/nls': {availableLanguages: {'*': 'zh-cn'}}
        }
    );
    require(['vs/editor/editor.main'], function () {
        g_editor = monaco.editor.create(
            document.getElementById(layoutid),
            {
                language: 'python',             //程序语言
                theme: theme,                   //界面主题
                value: code_str,                //初始文本内容
                automaticLayout: true,          //随布局Element自动调整大小                        
                minimap: {enabled: true},       //代码略缩图
                fontSize: 14,                   //字体大小
                //wordWrap: "on",               //自动换行，注意大小写
                //wrappingIndent: "indent",     //自动缩进
                //glyphMargin: true,            //字形边缘
                //useTabStops: false,           //tab键停留
                //selectOnLineNumbers: true,    //单击行号选中该行
                //roundedSelection: false,      //
                //readOnly: false,              // 只读
                //cursorStyle: 'line',          //光标样式
                //automaticLayout: false,       //自动布局
                //autoIndent:true,              //自动布局
                //quickSuggestions: false,
                //quickSuggestionsDelay: 500,   //代码提示延时
                contextmenu: false,
                scrollBeyondLastLine: true,
                //lineNumbersMinChars: 5,
                lineHeight: 24,
                //fontFamily:'Consolas',
                mouseWheelZoom: true,
                scrollbar: {
                    vertical: 1,
                    horizontal: 1,
                    useShadows: true,
                    horizontalSliderSize: 7,
                    verticalSliderSize: 7,
                    horizontalScrollbarSize: 7,
                    verticalScrollbarSize: 7,
                },
            }
        );
        g_editor.onDidChangeModelContent((v) => {
            on_modify(g_filename, org_datas[g_filename] != g_editor.getValue())
        });

    });

    //自适应大小，可以不要
    window.onresize = editor_layout;
    //编辑器加载成功后创建websocket连接
    //window.onload = init_webskt;
}

//自适应窗口大小
function editor_layout() {
    if (g_editor)
        g_editor.layout()
}

//设置主题风格 theme:vs-dark vs hc-black, fontsize:S M L XL XXL
function set_theme(theme, fontsize) {
    monaco.editor.setTheme(theme);

    const sizes = ['S', 'M', 'L', 'XL', 'XXL'];
    ind = sizes.indexOf(fontsize);
    if (ind < 0)
        return;
    fsize = 14 + 2 * ind;
    g_editor.updateOptions({ fontSize: fsize, lineHeight: fsize + 10, });
}

//设置代码文件
function load_file(file, txt) {
    g_filename = file;
    g_editor.setValue(txt);
}

//保存代码到本地文件, need_confirm为true时需要用户确认是否保存，否则不需要用户确认直接保存
function save_file(file, need_confirm) {
    // data = {
    //     'cmd':'savefile_rsp',
    //     'reqid':reqid,
    //     'file':file,
    //     'txt':datas[file],
    //     'errtxt':''
    // }
    // senddata(data);  

    //Bridge.callFromJs(file, datas[file], need_confirm);

    org_datas[file] = datas[file];
    on_modify(file, false)
}
//文件被修改
function on_modify(file, modified) {
    // data = {
    //     'cmd':'modify_nty',
    //     'file':file,
    //     'modified': modified
    // }
    // senddata(data);

    //Bridge.receiveFileStatus(file, modified);

    var tab = $(file);
    if (!tab)
        return;
    var btn = tab.children[0];
    if (!btn)
        return;

    if (modified)
        btn.className = 'modify_btn';
    else if (tab.id == currtab)
        btn.className = 'curr_btn';
    else if (tab.id == overtab)
        btn.className = 'over_btn';
    else
        btn.className = '';
}

//////////////////////////////////////////////////////////////////////////////
///标签栏管理
//////////////////////////////////////////////////////////////////////////////
// == 值比较  === 类型比较 $(id) ---->  document.getElementById(id)
function $(id){
    return typeof id === 'string' ? document.getElementById(id):id;
}
 
//全局字典 file->content
var datas = new Array();
var org_datas = new Array();

// 当前标签
var currtab = ""
var overtab = ""

// 切换标签
function switch_tab(newtab) {
    if (newtab == currtab)
        return;

    var n_tab = $(newtab.toString());
    if (!n_tab && newtab != "")
        return;
    
    if (n_tab){
        n_tab.className = 'current';
        var btn = n_tab.children[0];
        if (btn && btn.className != 'modify_btn')
            btn.className = 'curr_btn';
    }

    var c_tab = $(currtab.toString())
    if (c_tab){
        c_tab.className = '';
        var btn = c_tab.children[0];
        if (btn && btn.className != 'modify_btn')
            btn.className = '';

        datas[currtab] = g_editor.getValue();
        org_datas[name] = g_editor.getValue();
    }

    load_file(newtab, n_tab ? datas[newtab] : '');
    currtab = newtab; 

    Bridge.switchFile(newtab);
}

// 添加标签
function add_tab(name, value){
    if (name == "")
        return;
    if (datas.hasOwnProperty(name)){
        switch_tab(name);
        return;
    }

    //新建标签
    var tab = document.createElement("li");
    tab.id = name;
    tab.innerHTML = name.substr(name.lastIndexOf('/')+1);

    //新建关闭按钮
    var btn = document.createElement("a");
    btn.href = "#";
    btn.innerHTML = "x";
    btn.className = 'curr_btn'

    //添加按钮到标签上
    tab.appendChild(btn);
    //添加按钮到标签栏上
    $('tabs').appendChild(tab);

    //设置标签和按钮的单击事件
    tab.onclick = function(){
        switch_tab(this.id);
    }
    btn.onclick = function(){
        var tab = this.parentNode;
        if (tab.className == 'current')
        {
            var _tab = tab.nextElementSibling;
            if (!_tab)
                _tab = tab.previousElementSibling;
            switch_tab(_tab ? _tab.id : '');
        }
        if (org_datas[tab.id] != datas[tab.id])
            save_file(tab.id, true)

        delete datas[tab.id];
        delete org_datas[tab.id];
        tab.remove();
    }
    tab.onmouseover = function(){
        overtab = this.id;
        var btn = this.children[0];
        if (btn && btn.className != 'curr_btn' && btn.className != 'modify_btn')
            btn.className = 'over_btn';
    }
    tab.onmouseout = function(){ 
        overtab = "";
        var btn = this.children[0];
        if (btn && btn.className != 'curr_btn' && btn.className != 'modify_btn')
            btn.className = '';
    }

    //添加标签关联的数据
    datas[name] = value;
    org_datas[name] = value;
    //切换到新标签
    switch_tab(name);
}

//////////////////////////////////////////////////////////////////////////////
///websocket客户端
//////////////////////////////////////////////////////////////////////////////
// var ws = null;
//
// //判断浏览器是否内置了websocket
// function init_webskt() {
//     if (ws != null)
//         return;
//     if ('WebSocket' in window)
//         ws = new WebSocket("ws://localhost:8765");
//     else {
//         alert("error, WebSocket not exist!");
//         return;
//     }
//
//     //连接web socket成功触发
//     ws.onopen = function (evt) {
//     }
//     //断开web socket成功触发
//     ws.onclose = function (evt) {
//         ws = null;
//         setTimeout(1000);
//         init_webskt();
//     }
//     //web socket连接失败时触发
//     ws.onerror = function (evt) {
//     }
//
//     //当窗口关闭时，关闭websocket。防止server端异常
//     ws.onbeforeunload = function (evt) {
//         ws.close();
//     }
//
//     //接收web socket服务端数据时触发
//     ws.onmessage = function (evt) {
//         //alert(evt.data);
//         data = JSON.parse(evt.data);
//         if (data.cmd == 'openfile') {
//             add_tab(data.file, data.txt);
//         }
//         else if (data.cmd == 'settheme')
//             set_theme(data.theme, data.fontname, data.fontsize);
//         else if (data.cmd == 'savefile_req')
//             save_file(data.file);
//     };
// }
//
//
// //发送文本到websocket服务端
// function senddata(data) {
//     //init_webskt();
//     json_str = JSON.stringify(data);
//     ws.send(json_str);
//     //alert(json_str);
// }