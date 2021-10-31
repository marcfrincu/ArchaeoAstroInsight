myArgs = commandArgs(trailingOnly=TRUE)

downloadHWT <- function(HWTID) {
  if (nchar(HWTID) != 8) { stop('Incorrect HeyWhatsThat ID.') }

  ## Horizon metadata
  test <- readLines(paste0("http://www.heywhatsthat.com/iphone/pan.cgi?id=",HWTID))
  hor <- c()

  # Lat/Lon/Elev
  mypattern = '<div class=\"details_data\">([^<]*)</div>'
  datalines = grep(mypattern,test,value=TRUE)
  getexpr = function(s,g)substring(s,g,g+attr(g,'match.length')-1)
  gg = gregexpr(mypattern,datalines)
  matches = mapply(getexpr,datalines,gg)
  result = gsub(mypattern,'\\1',matches)
  names(result) = NULL
  result[c(1,2,4)]

  Lat <- as.numeric(strtrim(result[1],regexpr("&deg", result[1])[1]-1))
  if (substr(result[1],nchar(result[1]),nchar(result[2])) == "S") { Lat <- -Lat }
  Lon <- as.numeric(strtrim(result[2],regexpr("&deg", result[2])[1]-1))
  if (substr(result[2],nchar(result[2]),nchar(result[2])) == "W") { Lon <- -Lon }
  aux <- strtrim(result[4],regexpr("&nbsp;", result[4])[1]-1)
  Elev <- as.numeric(substr(aux,2,nchar(aux)))

  # Site Name
  grep("pan_top_title", test)
  mypattern = '<div id=\"pan_top_title\" class=\"ellipsis\" style=\"position: absolute; top: 46px; width: 296px\">([^<]*)</div>'
  datalines = grep(mypattern,test,value=TRUE)
  getexpr = function(s,g)substring(s,g,g+attr(g,'match.length')-1)
  gg = gregexpr(mypattern,datalines)
  matches = mapply(getexpr,datalines,gg)
  result = gsub(mypattern,'\\1',matches)
  names(result) = NULL
  Name <- result

  ## Horizon data
  hor.ex <- unique(substr(list.files(tempdir()),1,8)) # check if already downloaded

  if (sum(HWTID == hor.ex) == 0) {
    if (NROW(hor.ex) > 500) {
      # delete oldest
      details <- file.info(file.path(tempdir(),list.files(file.path(tempdir()))))
      details <- details[with(details, order(as.POSIXct(ctime))), ]
      files <- unique(substr(rownames(details),10,17))[1]
      files <- paste0(file.path(tempdir()),"/",c(files, paste0(files,"-0-1")), ".png")
      file.remove(files)
    }

    # download new one
    curdir <- getwd()
    setwd(tempdir())
    download.file(paste0('http://www.heywhatsthat.com/api/horizon.csv?id=',HWTID,'&resolution=.125'), mode ='wb', destfile=paste0(HWTID,'.csv'), quiet=T)
    setwd(curdir)
  }

  horizon <- read.csv(file.path(tempdir(), paste0(HWTID, '.csv')))

  ## Altitude Error
  delta <- 9.73  # 9.73m for SRTM data
  horizon$error <- rep(NA,NROW(data))
  for (i in 1:NROW(horizon)) {
    hor.alt <- horizon$altitude[i]
    delta.elev <- horizon$distance..m.[i] * tan( hor.alt * pi/180)
    aux0 <- atan( delta.elev / horizon$distance..m.[i]  ) * 180/pi
    aux1 <- atan( (delta.elev + delta) / horizon$distance..m.[i]  ) * 180/pi
    aux2 <- atan( (delta.elev - delta) / horizon$distance..m.[i]  ) * 180/pi
    horizon$error[i] <- mean(abs(c(aux1,aux2)-aux0))
  }

  # return result
  hor$metadata <- c()
  hor$metadata$ID <- HWTID
  hor$metadata$name <- Name
  hor$metadata$georef <- c(Lat, Lon, Elev); names(hor$metadata$georef) <- c('Lat','Lon', 'Elev'); dim(hor$metadata$georef) <- c(1,3)
  hor$metadata$elevation <- Elev

  hor$data <- data.frame(az = horizon$bin.bottom, alt = horizon$altitude, alt.unc = horizon$error)

  class(hor) <- "skyscapeR.horizon"
  return(hor)
}

plot.skyscapeR.horizon <- function(hor, show.az=F, xlim, ylim, obj, refraction=F) {
  if (missing(xlim)) { xlim <- c(0,360) }
  if (missing(ylim)) { ylim <- c(floor(min(hor$data$alt, na.rm=T))-5,45) }

  par(mar=c(2,1,1,1))
  plot(-99999,-99999, xlab = "", ylab = "", yaxs='i', xaxs='i', axes=F, lwd=5, xlim=xlim, ylim=ylim)
  scale <- mean(diff(pretty(seq(par('usr')[1],par('usr')[2]))))
  if (scale <= 1) { axis(1, at=seq(-40,360+40,0.1), lwd=0.2, labels=F) }
  if (scale <= 2 & scale > 1) { axis(1, at=seq(-40,360+40,0.5), lwd=0.2, labels=F) }
  if (scale <= 5 & scale > 2) { axis(1, at=seq(-40,360+40,1), lwd=0.5, labels=F) }
  if (scale <= 20 & scale > 5) { axis(1, at=seq(-40,360+40,5), lwd=0.5, labels=F) }
  if (scale < 90 & scale >= 10) { axis(1, at=seq(-40,360+40,10), lwd=0.5, labels=F) }

  if (show.az == T) {
    if (scale >= 10 & scale < 45) { scale <- 10 }
    if (scale >= 45 & scale < 90) { scale <- 45 }
    if (scale >= 90) { scale <- 90 }
    axis(1, at = seq(-90,360+90,scale), labels = seq(-90,360+90,scale), lwd=0)

  } else {

    ll <- c("N","NE","E","SE","S","SW","W","NW","N","NE","E","SE","S","SW","W","NW","N","NE","E","SE","S","SW","W","NW","N")
    axis(1, at = seq(-360,720,by=45), labels = ll, lwd=0.5)
  }

  # objects
  if (!missing(obj)) {
    ind <- sort(obj$decs[1,], decreasing=T, index.return=T)$ix
    for (i in ind) {
      if (length(obj$epoch)==1) {
        orb <- orbit(obj$decs[i], hor, res=0.5, refraction=refraction)
        lines(orb$az, orb$alt, col=obj$col[i], lty=obj$lty[i], lwd=obj$lwd[i])
      } else {
        orb1 <- orbit(obj$decs[3,i], hor, res=0.5)
        orb2 <- orbit(obj$decs[4,i], hor, res=0.5)
        lines(orb1$az, orb1$alt, col=obj$col[i], lty=obj$lty[i], lwd=obj$lwd[i])
        lines(orb2$az, orb2$alt, col=obj$col[i], lty=obj$lty[i], lwd=obj$lwd[i])
      }
    }
  }

  # Horizon line
  line(hor$data$az, hor$data$alt)
  x <- c(hor$data$az, rev(hor$data$az))
  y <- c(hor$data$alt, rep(-20,NROW(hor$data$az)))
  polygon(x , y, col=rgb(217/255,95/255,14/255,1), lwd=1.5)

  mtext(paste0('skyscapeR ', packageVersion('skyscapeR'),' (', substr(packageDescription('skyscapeR')$Date,1,4),')'), side=3, at=par('usr')[2], cex=0.5, adj=1)
  box()
}

hor2alt = function(hor, az) {
  alt <- approx(c(hor$data$az-360,hor$data$az,hor$data$az+360), rep(hor$data$alt,3), xout=az)$y
  alt <- round(alt, 2)

  if (!is.null(hor$data$alt.unc)) {
    hh <- approx(c(hor$data$az-360,hor$data$az,hor$data$az+360), rep(hor$data$alt.unc,3), xout=az)$y
    alt.unc <- round(hh, 2)

    #alt <- data.frame(alt=alt, alt.unc=alt.unc)
  }
  return(alt)
}

hor <- downloadHWT(myArgs[1])
#plot(hor)
output = hor2alt(hor, as.numeric(myArgs[2]))
#output

cat(output)