suppressMessages(library(synthpop))
a <- commandArgs(trailingOnly = TRUE)
inp <- a[1]; out <- a[2]; m <- as.integer(a[3]); seed <- as.integer(a[4]); cats <- strsplit(a[5], ",")[[1]]
d <- read.csv(inp, colClasses = "character")
for (c in names(d)) d[[c]] <- if (c %in% cats) factor(d[[c]]) else as.numeric(d[[c]])
pm <- NULL
if (all(c("puma", "occ") %in% names(d))) {
  vs <- c("age", "sex", "race", "native", "schl", "mar", "cow", "occ", "puma", "wkhp", "wagp", setdiff(names(d), c("age", "sex", "race", "native", "schl", "mar", "cow", "occ", "puma", "wkhp", "wagp")))
  d <- d[, vs]
  s0 <- syn(d, method = "cart", m = 0, print.flag = FALSE, maxfaclevels = 200)
  pm <- s0$predictor.matrix
  pm["puma", "occ"] <- 0
}
t0 <- Sys.time()
s <- if (is.null(pm)) syn(d, m = m, seed = seed, print.flag = FALSE, maxfaclevels = 200) else
  syn(d, m = m, seed = seed, print.flag = FALSE, maxfaclevels = 200, predictor.matrix = pm)
cat("secs", as.numeric(difftime(Sys.time(), t0, units = "secs")), "\n")
sy <- if (m == 1) list(s$syn) else s$syn
for (i in seq_along(sy)) write.csv(sy[[i]], sprintf("%s_%d.csv", out, i - 1), row.names = FALSE)
