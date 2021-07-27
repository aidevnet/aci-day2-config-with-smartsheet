# How to use

There are 2 files that need to be updated when adding tabs, `scripts.js` and `index.html`.

## HTML file

To update the HTML file, you must use the format below, the value of i in  `ChangeTab(i)` must be unique as it's used to change the Iframe. The tab name can be changed to whatever is neccesary, and using any icon from the `icons/` folder for the tab icon is possible.

```html
<li class="sidebar__item" onclick="ChangeTab(0)">
    <div class="icon"><img src="Resources/icons/cloud.svg" class="icon"></div>
    <div class="side-bar-text hide ">TAB NAME</div>
</li>

```

## JS file

To update the JS file, use the index set in the `ChangeTab(i)` function. You can either edit the existing lines for your tabs or add a new URL using the snippet below, changing the index of `i` and the `SMARTSHEETURL` to the url of the smartsheet.

```javascript
    page[i] = "SMARTSHEETURL"
```


*** Save it and start the frontend by opening index.html in an Internet browser ***
