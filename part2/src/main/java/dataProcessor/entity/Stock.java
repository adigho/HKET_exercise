package dataProcessor.entity;

public class Stock {
    private String id;
    private String name;

    public Stock() {

    }

    public Stock(String id, String name){
        this.id = id;
        this.name = name;
    }

    public String getId(){
        return id;
    }

    public String getName(){
        return name;
    }

    public void setID(String id){
        this.id = id;
    }

    public void setName(String name){
        this.name = name;
    }
}
