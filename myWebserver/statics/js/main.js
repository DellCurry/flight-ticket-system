function show(num) {
            var container = document.getElementsByClassName('content')[0];
            var divlist = container.getElementsByTagName('div');
            for (var i = 0; i < divlist.length; i++) {
                var classNode = document.createAttribute('class');
                classNode.value = 'tab-content';
                divlist[i].setAttributeNode(classNode);
                divlist[i].style.display="none"; 
            }
            var pageDiv = document.getElementById('content' + num);
  				  pageDiv.style.display="";
        }
