package dataProcessor.controller;

import dataProcessor.entity.Stock;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping(produces = MediaType.APPLICATION_JSON_VALUE)

public class stockController {

    @GetMapping("/stocks/{id}")
    public Stock getStock(@PathVariable("id") String id){
        Stock stock = new Stock();
        stock.setID(id);
        stock.setName("Noe");

        return stock;
    }

}
