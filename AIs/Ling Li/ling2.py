from monopyly import *
from .ling import LingAI

class Ling2AI(LingAI):
    def __init__(self):
        '''
        The 'constructor'.
        '''
        super().__init__()

        self._cash_reserve = 300
        self.properties_we_dont_like = [Square.Name.ELECTRIC_COMPANY, Square.Name.WATER_WORKS]

        # dictionary of players to the property + offer made
        self._offers_made = {}
        # list of the colour sets we are looking to match
        self.sets_we_have = []
        self._is_eminent_domain = False

        # rank the order of properties we want to mortgage in order
        self.property_mortgage_list = [Square.Name.ELECTRIC_COMPANY, Square.Name.WATER_WORKS,
                                       Square.Name.KINGS_CROSS_STATION, Square.Name.LIVERPOOL_STREET_STATION,
                                       Square.Name.FENCHURCH_STREET_STATION, Square.Name.MARYLEBONE_STATION,
                                       Square.Name.OLD_KENT_ROAD, Square.Name.WHITECHAPEL_ROAD,
                                       Square.Name.THE_ANGEL_ISLINGTON, Square.Name.EUSTON_ROAD,
                                       Square.Name.PENTONVILLE_ROAD, Square.Name.MAYFAIR, Square.Name.PARK_LANE,
                                       Square.Name.PALL_MALL, Square.Name.WHITEHALL, Square.Name.NORTHUMBERLAND_AVENUE,
                                       Square.Name.LEICESTER_SQUARE, Square.Name.COVENTRY_STREET, Square.Name.PICCADILLY,
                                       Square.Name.BOND_STREET, Square.Name.OXFORD_STREET, Square.Name.REGENT_STREET,
                                       Square.Name.BOW_STREET, Square.Name.MARLBOROUGH_STREET, Square.Name.VINE_STREET,
                                       Square.Name.STRAND, Square.Name.FLEET_STREET, Square.Name.TRAFALGAR_SQUARE]

        self.properties_we_like = [Square.Name.KINGS_CROSS_STATION, Square.Name.LIVERPOOL_STREET_STATION,
                                   Square.Name.FENCHURCH_STREET_STATION, Square.Name.MARYLEBONE_STATION,
                                   Square.Name.STRAND, Square.Name.FLEET_STREET, Square.Name.TRAFALGAR_SQUARE,
                                   Square.Name.BOND_STREET, Square.Name.OXFORD_STREET, Square.Name.REGENT_STREET,
                                   Square.Name.BOW_STREET, Square.Name.MARLBOROUGH_STREET, Square.Name.VINE_STREET]

        self.property_set_preferences = [ PropertySet.STATION, PropertySet.ORANGE, PropertySet.RED, PropertySet.YELLOW,
                                          PropertySet.GREEN, PropertySet.LIGHT_BLUE, PropertySet.DARK_BLUE,
                                          PropertySet.PURPLE, PropertySet.UTILITY]

        self.properties_we_dont_like = [Square.Name.ELECTRIC_COMPANY, Square.Name.WATER_WORKS]
        self.properties_bought = 0
        self.have_get_out_of_jail_card = 0
        self.money_to_be_taken = 0

    def get_name(self):
        '''
        Returns the name shown for this AI.
        '''
        return "zizzling"

    def landed_on_unowned_property(self, game_state, player, property):
        '''
        Called when we land on an unowned property. We always buy it if we
        can while keeping a small cash reserve.
        '''
        if property.name in self.properties_we_dont_like:
            return PlayerAIBase.Action.DO_NOT_BUY

        if player.net_worth > (self._cash_reserve + property.price):
            self.properties_bought = self.properties_bought + 1
            return PlayerAIBase.Action.BUY
        else:
            return PlayerAIBase.Action.DO_NOT_BUY

    def propose_deal(self, game_state, player):
        for property_name in self.properties_we_like:
            property = game_state.board.get_square_by_name(property_name)
            if(property.owner is player or property.owner is None):
                continue

            # property is owned by someone else
            # put cheeky offer

            prev_offers = self._offers_made.get(property.owner, None)
            if prev_offers is None:
                self._offers_made[property.owner] = {}
                price_offered = property.price + 1
            else:
                prev_price_offered = prev_offers.get(property_name, None)
                if prev_price_offered is None:
                    price_offered = property.price + 1
                else:
                    # TODO: offer 10% increments
                    price_offered = prev_price_offered + property.price * 0.1

            if player.state.cash - self._cash_reserve > price_offered:
                self._offers_made[property.owner][property_name] = price_offered
                Logger.log("Offering: {0}".format(price_offered))
                return DealProposal(
                    properties_wanted=[property],
                    maximum_cash_offered=price_offered,
                    propose_to_player=property.owner)
        return None

    def deal_proposed(self, game_state, player, deal_proposal):
        '''
        Called when a deal is proposed by another player.
        '''
        # TODO: check to see if the person who is making the offer has
        # a similar colour, if yes, then check how much cash they have
        # if they lots of cash then don't sell
        # if it makes them close to bankrupt (ie < our reserve, then sell for as much as possible)


        # We only accept deals for single properties wanted from us...
        if len(deal_proposal.properties_offered) > 0:
            return DealResponse(DealResponse.Action.REJECT)
        #if len(deal_proposal.properties_wanted) > 1:
            #return DealResponse(DealResponse.Action.REJECT)

        # loop through all properties
        property_prices = 400
        for property in deal_proposal.properties_wanted:
            # check that the other player does not already own a property from that set
            for property_subset in property.property_set.properties:
                prop = game_state.board.get_square_by_name(property_subset.name)
                if prop.owner == player.name:
                    return DealResponse(DealResponse.Action.REJECT)
            property_prices += (property.price * 2) + 1

        # We'll accept as long as the price offered is greater than
        # the original selling price..
        return DealResponse(
            action=DealResponse.Action.ACCEPT,
            minimum_cash_wanted=property_prices)

    def build_houses(self, game_state, player):
        '''
        Gives us the opportunity to build houses.
        '''
        # We find the first set we own that we can build on...
        # go through our preferred list of sets and decide on which to build on:
        for owned_set in self.property_set_preferences:
            if owned_set in player.state.owned_unmortgaged_sets:
                # We can't build on stations or utilities, or if the
                # set already has hotels on all the properties...
                if not owned_set.can_build_houses:
                    continue

                # We see how much money we need for one house on each property...
                for houses_to_build in range(owned_set.number_of_properties, 1, -1):
                    cost = owned_set.house_price * houses_to_build
                    if player.state.cash > (self._cash_reserve + cost):
                        # We build one house on each property...
                        property_build_list = [(p, 1) for p in owned_set.properties]
                        for i in range(len(owned_set.properties), houses_to_build, -1):
                            property_build_list.pop()
                        Logger.log("Building properties: {0}/{1}".format(houses_to_build, len(owned_set.properties)))
                        return property_build_list


        # We can't build...
        return []

    def players_birthday(self):
        ''' implement this as required or else be fined harshly!
        '''
        return "Happy Birthday!"

    def mortgage_properties(self, game_state, player):
        if player.state.cash < self._cash_reserve or player.state.cash - self.money_to_be_taken < self._cash_reserve:
            ''' look for minimum number of properties to mortgage to ensure we have min cash in hand
            '''
            mortgage_total = 0
            properties_to_mortgage = {}
            for prop in player.state.properties:
                if not prop.is_mortgaged:
                    properties_to_mortgage[self.property_mortgage_list.index(prop.name)] = prop
            # now we have the list of properties we can mortgage, work through them all till we have enough money
            return_property_list = []
            for k in sorted(properties_to_mortgage.keys()):
                return_property_list.append(properties_to_mortgage[k])
                mortgage_total += properties_to_mortgage[k].mortgage_value
                if player.state.cash + mortgage_total - self.money_to_be_taken >= self._cash_reserve:
                    break
            return return_property_list
        return []

    def unmortgage_properties(self, game_state, player):
        ''' only unmortgage if we have spare cash and no more properties we like to buy?
        '''
        cash_buffer = self.get_max_price_of_list_properties(game_state, self.properties_we_like)
        # get the list of properties we can mortgage
        properties_to_unmortgage = {}
        for prop in player.state.properties:
            if prop.is_mortgaged:
                    properties_to_unmortgage[self.property_mortgage_list.index(prop.name)] = prop

        return_property_list = []
        # no loop through and check that we have
        current_cash = player.state.cash - self._cash_reserve
        for k in sorted(properties_to_unmortgage.keys(), reverse=True):
            current_cash -= properties_to_unmortgage[k].price * 1.1
            if current_cash > 0:
                return_property_list.append(properties_to_unmortgage[k])
            else:
                break

        return return_property_list

    def money_will_be_taken(self, player, amount):
        self.money_to_be_taken = amount


    def get_max_price_of_list_properties(self, game_state, list_of_properties):
        max_price = 0
        for prop in list_of_properties:
            if game_state.board.get_square_by_name(prop).price > max_price:
                max_price = game_state.board.get_square_by_name(prop).price
        return max_price



    def start_of_turn(self, game_state, player):
        self.money_to_be_taken = 0
        '''
        work out how many properties are left/freely available, to determine what part of the game
        we are in. Used for the get out of jail strategy
        '''
        self.properties_bought = 0
        for square in game_state.board.squares:
            if isinstance(square, Property):
                if square.owner is not None:
                    self.properties_bought += 1

        return


    def got_get_out_of_jail_free_card(self):
        self.have_get_out_of_jail_card += 1

    def get_out_of_jail(self, state, player):
        '''
        Called in the player's turn, before the dice are rolled, if the player
        is in jail.

        There are three possible return values:
        PlayerAIBase.Action.BUY_WAY_OUT_OF_JAIL
        PlayerAIBase.Action.PLAY_GET_OUT_OF_JAIL_FREE_CARD
        PlayerAIBase.Action.STAY_IN_JAIL

        Buying your way out of jail will cost £50.

        The default action is STAY_IN_JAIL.
        '''
        if self.properties_bought > 20:
            return PlayerAIBase.Action.STAY_IN_JAIL
        elif len(player.state.get_out_of_jail_free_cards) > 0:
        #elif self.have_get_out_of_jail_card > 0:
        #    self.have_get_out_of_jail_card -= 1
            return PlayerAIBase.Action.PLAY_GET_OUT_OF_JAIL_FREE_CARD
        else:
            return PlayerAIBase.Action.BUY_WAY_OUT_OF_JAIL

    def auction_result(self, status, property, player, amount_paid):
        #if status == PlayerAIBase.Action.AUCTION_SUCCEEDED:
        #    self.properties_bought = self.properties_bought + 1
        return



