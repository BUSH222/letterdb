// RocketCake Menu implementation
// (c) by Nikolaus Gebhardt / Ambiera e.U.
// parameters:
// elementid: Element id of the root menu item
// animations: combination of 'fadeMenus', 'moveHeight'
// openViaMouseHovering: if set to true, on desktop, open menu already via mouse hovering. If set to false, only close and open the menu when clicked or touched.
function wsp_menu(elementid, menuidsuffix, panepadding, animations, openViaMouseHovering)
{
	this.menuElementSubMenuParent = document.getElementById(elementid);
	this.menuElementEntryHolder = null;
	
	if (this.menuElementSubMenuParent)
	{
		var divs = this.menuElementSubMenuParent.getElementsByTagName('div');
		if (divs.length)
		{
			this.menuElementEntryHolder = divs[0];		
			
			if (this.menuElementEntryHolder && this.menuElementEntryHolder.id.indexOf('_menualignmentwrapper') > -1)
			{
				// menu has an alignment wrapper, so the entry holder is below it
				divs = this.menuElementEntryHolder.getElementsByTagName('div');
				if (divs.length)
				{
					this.menuElementSubMenuParent = this.menuElementEntryHolder;
					this.menuElementEntryHolder = divs[0];					
				}
			}				
		}	
	}
	
	this.rootMenuElements = new Array();
	this.menuPanes = new Array();
	this.menuidsuffix = menuidsuffix;
	this.panepadding = panepadding;
	this.initialClientHeight = 0;
	this.currentlyVisibleMenuPane = null;
	this.openViaMouseHovering = openViaMouseHovering; 
	WspMenusLastTimeClicked = 0;  // global if using more than one menu
	this.LastOpenedSubMenu = null;
	this.UseAnimation = animations != null;
	this.EnabledAnimations = animations;
	
	try {
		if (wsp_allmenus == null)
			wsp_allmenus = new Array();
	} catch(e)
	{
		wsp_allmenus = new Array();
	}
	
	wsp_allmenus.push(this);
	
	var me = this;
	document.onclick = function() { me.clickedOutside(); };

	if (this.menuElementSubMenuParent != null)
		this.menuElementSubMenuParent.style.overflow = "visible";

	if (this.menuElementEntryHolder != null)
		this.menuElementEntryHolder.style.overflow = "hidden";
	
	
	this.createMenuForItem = function(menuelementid, elementData)
	{
		var e = document.getElementById(menuelementid);
		if (e == null)
			return;
			
		this.rootMenuElements.push(e);
		var menupane = this.createMenuElements(e, elementData, false);
		this.menuPanes.push(menupane);
		
		var me = this;
		e.onclick = function(e)  { me.onMenuitemHovered(this, true); };
		if (this.openViaMouseHovering)
			e.onmouseover = function(e) { me.onMenuitemHovered(this, false); };
	}
	
	
	this.createMenuElements = function(htmlelement, elementData, issubmenu)
	{
		if (htmlelement == null)
			return;
			
		if (elementData == null || elementData.length == 0)
			return;
			
		var me = this;
		var menupane = document.createElement("div");
		
		menupane.style.position = "absolute";		
		menupane.style.left = (htmlelement.offsetLeft) + "px";
		menupane.style.top = (htmlelement.clientHeight + this.panepadding) + "px";
		menupane.style.overflow = "visible";
		menupane.style.zIndex = 10;
		menupane.id = this.menuidsuffix + "_pane";	
		menupane.creationParentMenuElement = htmlelement;
		
		menupane.style.visibility = 'hidden';	
		menupane.style.display = 'block';	
		
		if (this.UseAnimation && this.isUsingFadeMenuPaneAnimations())
			menupane.style.transition = "opacity 0.5s ease-out";
		
		this.menuElementSubMenuParent.appendChild(menupane);	
		
		menupane.subMenus = new Array();
		
		var maxWidth = 0;
		var maxHeight = 0;
		
		var aentries = new Array();
		
		var submenusExist = false;
		
		for (var i=0; i<elementData.length; i+=3)
		{			
			var elementContent = elementData[i+1];
			var elementTarget  = elementData[i+2];
			
			// test width of text
			var testElement = document.createElement("span");
			var textToMeasure = elementData[i];
			
			if (elementContent instanceof Array )
			{
				// has a sub menu
				
				// for elements with submenu and sub menu indicator, only measure the inner text,
				// which is the second appearing span				
				
				var beginText = textToMeasure.indexOf('<span', textToMeasure.indexOf('<span')+1);
				var endText = textToMeasure.indexOf('</span><span style="display:inline-block;', beginText);
				
				textToMeasure = textToMeasure.substring(beginText, endText);
			}
			
			testElement.innerHTML = textToMeasure;
			this.menuElementEntryHolder.appendChild(testElement);
						
			var width = testElement.offsetWidth;
			var height = testElement.offsetHeight;
			this.menuElementEntryHolder.removeChild(testElement);
			
			// now create real element		
			var aentry = document.createElement("a");			
			var menuentry = document.createElement("div");
			
			var txt = null;
			
			if (elementData[i] != '-')
				//txt = document.createTextNode(elementData[i]);
				menuentry.innerHTML = elementData[i];
			else
			{
				txt = document.createElement('hr');
				txt.id = this.menuidsuffix + "_hr";
			}
			
			aentry.appendChild(menuentry);
			if (txt != null)
				menuentry.appendChild(txt);
			menupane.appendChild(aentry);
						
			if (elementContent instanceof Array )
			{
				// sub menu
				var submenu = this.createMenuElements(menupane, elementContent, true);
				menupane.subMenus.push(submenu);
							
				menuentry.onclick = function(me, submenu) { return function() { me.onSubMenuEntryHovered(submenu); } }(me, submenu);
				menuentry.onmouseover = function(me, submenu) { return function() { me.onSubMenuEntryHovered(submenu); } }(me, submenu);
				
				submenusExist = true;
			}
			else
			{
				// normal link
				aentry.href = elementContent;
				
				if (elementTarget != null && elementTarget != '')
					aentry.setAttribute('target', elementTarget);
			}
			
			menuentry.id = this.menuidsuffix + "_entry";
			aentries.push(menuentry);
					
			maxWidth = Math.max(maxWidth, width);
			maxHeight += height; //txt.clientHeight;
		}
		
		if (submenusExist)
			maxWidth += 20; // add space for the arrow right symbol for submenus
		
		for (var j=0; j<aentries.length; ++j)
			aentries[j].style.width = maxWidth + "px";
			
		for (var j=0; j<menupane.subMenus.length; ++j)
			menupane.subMenus[j].style.left = (htmlelement.offsetLeft + maxWidth + panepadding*2) + "px";
		
		maxWidth += panepadding*2;
		menupane.style.width = maxWidth + "px"; 
		menupane.style.whiteSpace = 'nowrap'; // in case for embedded images
		menupane.aentries = aentries;
		
		this.setStylesForVisibilityOfMenuPane(menupane, false);
						
		return menupane;
	}
	
	this.closeAllMenus = function()
	{
		for (var i=0; i<wsp_allmenus.length; ++i)
		{
			var m = wsp_allmenus[i];
			m.showMenuPaneWithIndex(-1);
			
			// also close sub menus
			m.closeOpenSubMenu();
		}		
	}
	
	this.closeOpenSubMenu = function()
	{
		if (this.LastOpenedSubMenu != null)
		{
			this.setStylesForVisibilityOfMenuPane(this.LastOpenedSubMenu, false);
			
			this.LastOpenedSubMenu = null;
		}
	}
	
	this.isMenuPaneWithIndexOpen = function(i)
	{
		var paneToCheck = null;
		if (i >= 0 && i < this.menuPanes.length)
			paneToCheck = this.menuPanes[i];
		return (paneToCheck && 	this.currentlyVisibleMenuPane === paneToCheck);
	}
	
	this.showMenuPaneWithIndex = function(i)
	{
		if (this.currentlyVisibleMenuPane)
			this.setStylesForVisibilityOfMenuPane(this.currentlyVisibleMenuPane, false);
				
		var newpane = null;
		if (i >= 0 && i < this.menuPanes.length)
			newpane = this.menuPanes[i];
		
		this.currentlyVisibleMenuPane = newpane;
		
		if (newpane)
		{
			this.setStylesForVisibilityOfMenuPane(newpane, true);
			
			// also, update position
			var htmlelement = newpane.creationParentMenuElement;
			newpane.style.left = (htmlelement.offsetLeft) + "px";
			newpane.style.top = (htmlelement.clientHeight) + "px";
			this.ensureNotOutsideOfScreen(newpane);
		}
	}
	
	// main menu item hovered
	this.onMenuitemHovered = function(itemHovered, actuallyThisWasAClick)
	{
		WspMenusLastTimeClicked = this.getTimeMs();
			
		// check if a root menu item has been hovered. If so, show its menu
		for (var i=0; i<this.rootMenuElements.length; ++i)
		{
			if (itemHovered === this.rootMenuElements[i])
			{
				var closeMenuAgain = false;
				if (actuallyThisWasAClick && !this.openViaMouseHovering && this.isMenuPaneWithIndexOpen(i))
					closeMenuAgain = true;
				
				this.closeAllMenus();
				
				if (!closeMenuAgain)
					this.showMenuPaneWithIndex(i);
				break;
			}
		}
	}
	
	// menu entry hovered, probably show sub menu
	this.onSubMenuEntryHovered = function(submenu)
	{
		this.closeOpenSubMenu();
		
		this.setStylesForVisibilityOfMenuPane(submenu, true)
		
		this.LastOpenedSubMenu = submenu;
		
		WspMenusLastTimeClicked = this.getTimeMs();
	}
	
	
	this.clickedOutside = function()
	{
		if ((this.getTimeMs() - WspMenusLastTimeClicked)< 250)
			return;
			
		this.closeAllMenus();
	}
	
	
	this.getTimeMs = function()
	{
		var d = new Date();
		return d.getTime();
	}
	
	this.ensureNotOutsideOfScreen = function(elem)
	{
		try
		{
			var pos = this.getElementAbsPosition(elem);
			var scrollbarMargin = 20;
			
			if (pos.left + pos.width > window.innerWidth - scrollbarMargin  )
			{
				var deltaX = (pos.left + pos.width) - (window.innerWidth - scrollbarMargin);
				if (pos.left - deltaX < 0)
					deltaX += pos.left - deltaX;
				
				var currentPos = parseInt(elem.style.left);				
				elem.style.left = (currentPos - deltaX) + 'px';
			}
		}
		catch(e)
		{
		}
	}
	
	this.setStylesForVisibilityOfMenuPane = function(menupane, show)
	{
		if (show)
		{
			if (!this.UseAnimation)
				menupane.style.display = 'block'; // reduces viewport size if animations are not necessary
			
			menupane.style.visibility = 'visible';	

			if (this.UseAnimation && this.isUsingFadeMenuPaneAnimations())
				menupane.style.opacity = 1;		

			if (this.UseAnimation && this.isUsingMoveHeightAnimations())
				for (var j=0; j<menupane.aentries.length; ++j)
				{
					menupane.aentries[j].style.transition = "margin 0.5s ease";
					menupane.aentries[j].style.marginTop = '0px';							
				}
		}
		else
		{
			// hide
			if (!this.UseAnimation)
				menupane.style.display = 'none'; // reduces viewport size if animations are not necessary
			
			menupane.style.visibility = 'hidden';
			
			if (this.UseAnimation && this.isUsingFadeMenuPaneAnimations())
				menupane.style.opacity = 0;		

			if (this.UseAnimation && this.isUsingMoveHeightAnimations())
				for (var j=0; j<menupane.aentries.length; ++j)
					menupane.aentries[j].style.marginTop = (10 + j*-10) + 'px';	
		}
	}
	
	this.isUsingMoveHeightAnimations = function()
	{
		return this.EnabledAnimations && this.EnabledAnimations.indexOf('moveHeight') >= 0;
	}
	
	this.isUsingFadeMenuPaneAnimations = function()
	{
		return this.EnabledAnimations && this.EnabledAnimations.indexOf('fadeMenus') >= 0;
	}
		
	this.getElementAbsPosition = function(element) 
	{
		var top = 0;
		var left = 0;
		var width = element.offsetWidth;
		var height = element.offsetHeight;	
		
		do 
		{
			top += element.offsetTop  || 0;
			left += element.offsetLeft || 0;
			element = element.offsetParent;
		} 
		while(element);
		
		// this does the same but doesn't work on older browsers:
		// var rct = element.getBoundingClientRect();
		// top = rct.top;
		// left = rct.left;
		// width = rct.right - rct.left;
		// height = rct.bottom - rct.top;
		
		var obj = new Object();
		
		obj.top = top;
		obj.left = left;
		obj.width = width;
		obj.height = height;
		
		return  obj;
	}
	
} // end function wsp_menu