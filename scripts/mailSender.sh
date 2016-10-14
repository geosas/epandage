#!/bin/sh 

# $1 -> email,
# $2 -> temps de traitement


echo "Sending mail..."
/usr/sbin/sendmail -t <<EOT
From: no-replay@geowww.agrocampus-ouest.fr
To: $1
Subject: Résultat du traitement de zonage des pentes
MIME-Version: 1.0
Content-Type: multipart/related;boundary="XYZ"

--XYZ
Content-Type: text/html; charset=utf-8
Content-Transfer-Encoding: 8bit

<html>

<body> <a href="http://geowww.agrocampus-ouest.fr"><img src='http://integrer.agrocampus-ouest.fr/igagrocampus-ouest.fr/images/integrer-ao/logo.png' align='right' /> </a>
    <div align='left'>
        <h2> Résultats du traitement de zonage des pentes </h2>
        <br></br>
        <h3>Le traitement et terminé avec succès ! Temps de traitement: $2 </h3>

        <p>Pour visualiser la carte sur un visualiseur avancé <a style="font-weight:bold;" href="http://geowww.agrocampus-ouest.fr/mapfishapp/?wmc=http%3A%2F%2Fgeowww.agrocampus-ouest.fr%2Fmapfishapp%2Fws%2Fwmc%2Fgeodoc60527d732c2d6ef089ea8431c8e613d9.wmc">Cliquez ici</a> </p>
	
	<p>Pour la visualiser sur un visualiseur mobile <a style="font-weight:bold;" href="http://geowww.agrocampus-ouest.fr/sviewer/?lb=1&title=Zonage+des+pentes+a+100m+des+cours+d%27eau+en+Bretagne&wmc=http%3A%2F%2Fgeowww.agrocampus-ouest.fr%2Fmapfishapp%2Fws%2Fwmc%2Fgeodoc60527d732c2d6ef089ea8431c8e613d9.wmc">Cliquez ici</a> <p>
        <br></br>
        
        <br></br>
        <p>---------------------------------------------------------------</p>

        <br></br>
        <p>Message généré automatiquement. Ne pas répondre à ce message !</p>
    </div>
</body>

</html>

--XYZ
EOT
echo "Mail sent, OK!"
