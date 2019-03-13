(function(){

	var tabslist = document.querySelectorAll('.tabs');

	tabslist.forEach(function(tab){
		var btns = tab.querySelectorAll('[data-tab]');
		btns.forEach(function(a){
			console.log(`#${a.dataset.tab}`,tab);
			a.addEventListener('click', function(e){
				console.log(tab);
				var divs = tab.querySelectorAll('.tabs-content > div');
				divs.forEach((div) => div.style.display="none");
				btns.forEach((btn) => btn.classList.remove("active"));
				a.classList.add("active");
				if(tab.querySelector(`#${a.dataset.tab}`)) tab.querySelector(`#${a.dataset.tab}`).style.display = "";
			});
		});
		//console.log(tab.querySelectorAll('[data-tab]'));

	});

}())